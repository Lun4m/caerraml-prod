import os
from datetime import datetime
from pathlib import Path

import click
import earthkit.data as ekd
import tqdm
from caerra_prep.main import Date, Domain, common_cli_params


def split_file(file: Path, output_dir: Path, stream: bool = False):
    fieldlist = ekd.from_source("file", str(file), stream=stream).to_fieldlist()

    surface_analysis = output_dir / f"{file.stem}_sfc_an.grib2"
    surface_forecast = output_dir / f"{file.stem}_sfc_fc.grib2"
    height_level = output_dir / f"{file.stem}_hl_an.grib2"
    forecast_prev = output_dir / f"{file.stem}_sfc_fc_prev.grib2"

    with (
        ekd.create_target("file", surface_forecast) as sfc_fc,
        ekd.create_target("file", surface_analysis) as sfc_an,
        ekd.create_target("file", height_level) as hl,
        ekd.create_target("file", forecast_prev) as fc_prev,
    ):
        for field in tqdm.tqdm(fieldlist):
            levtype, type_ = field.metadata(("levtype", "type"))

            if levtype == "hl" and type_ == "an":
                hl.write(field)

            if levtype == "sfc" and type_ == "an":
                sfc_an.write(field)

            if levtype == "sfc" and type_ == "fc":
                time: datetime = field.time.valid_datetime()
                if time.hour == 21:
                    fc_prev.write(field)
                else:
                    sfc_fc.write(field)


@click.command(context_settings={"show_default": True})
@common_cli_params
def split_inference_output(date_cli: datetime | None, lookback: int):
    date = Date(date_cli, lookback)

    inputs_dir = Path(os.environ["CAERRA_OUTPUT_DIR"]) / date.str
    output_dir = Path(os.environ["CAERRA_OUTPUT_DIR"]) / date.str / "split"

    for domain in Domain:
        for file in inputs_dir.glob(f"{domain}*"):
            split_file(file, output_dir)
