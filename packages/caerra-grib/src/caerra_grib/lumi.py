import functools
import multiprocessing as mp
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click
import earthkit.data as ekd
import numpy as np
from caerra_prep.main import Domain

VARIABLES_TO_CLIP = ["2r", "tcc"]


class Field:
    def __init__(self, field: ekd.Field):
        self.field = field
        self.values = field.values
        # Valid datetime returns the base+step for forecasts,
        # so they are aligned with the analysis
        self.time: datetime = field.time.valid_datetime()
        self.date = self.time.date()

        name, _type, level = field.metadata(("shortName", "type", "levtype"))

        self.name = name
        self.type = _type
        self.level = level

    def set(self, values: dict):
        updated = self.field.set(values)
        self.field = updated


def write_fields(
    fields: list[Field],
    outdir: Path,
    temperature: list[Field],
    domain: Domain,
    member: str,
):
    # scripts/mars/archive.sh expects the format: .../YYYY-mm-dd/split
    outdir /= "split"
    outdir.mkdir(parents=True, exist_ok=True)

    stem = f"{domain}_m{member}"

    surface_analysis = outdir / f"{stem}_sfc_an.grib2"
    surface_forecast = outdir / f"{stem}_sfc_fc.grib2"
    height_level = outdir / f"{stem}_hl_an.grib2"
    forecast_prev = outdir / f"{stem}_sfc_fc_prev.grib2"

    # index for temperature field
    idx = 0

    with (
        ekd.create_target("file", surface_forecast) as sfc_fc,
        ekd.create_target("file", surface_analysis) as sfc_an,
        ekd.create_target("file", height_level) as hl_an,
        ekd.create_target("file", forecast_prev) as fc_prev,
    ):
        for field in fields:
            # Switch from Physical to ML suite
            update = {"metadata.suiteName": domain.suite_name()}

            if field.name in VARIABLES_TO_CLIP:
                values = np.clip(field.values, 0.0, 100.0)
                update["values"] = values
            elif field.name == "mn2t":
                values = np.minimum(field.values, temperature[idx].values)
                update["values"] = values
            elif field.name == "mx2t":
                values = np.maximum(field.values, temperature[idx].values)
                update["values"] = values
                idx += 1

            if field.type == "an":
                update["metadata.significanceOfReferenceTime"] = 0

                if member == "00":
                    update["metadata.productDefinitionTemplateNumber"] = 0

                out = hl_an if field.level == "hl" else sfc_an
            else:
                if member == "00":
                    update["metadata.productDefinitionTemplateNumber"] = 8
                # surface forecast fields
                # NOTE: valid time is used here,
                # 00 == 21 (from previous day) + 3 hours
                out = fc_prev if field.time.hour == 00 else sfc_fc

            field.set(update)
            out.write(field.field)


# We have 1 year data, separated by month and member number
# This function takes a month file, YYYY-mm_n(memmber).grib2
#
# This currently only filters the single day output from normal inference
def split_by_day(domain: Domain, member: str, file: Path, outdir: Path):
    fields = ekd.from_source("file", str(file), stream=True).to_fieldlist()

    curr_date = None
    outfields = []
    temps = []

    # Need to copy it here because the loop modifies it
    outdir_ = outdir
    for ekdfield in fields:
        field = Field(ekdfield)

        if curr_date is None or field.date > curr_date:
            if len(outfields) > 0:
                print(f"Saving {len(outfields)} fields for time = {curr_date}")
                write_fields(outfields, outdir_, temps, domain, member)
                outfields = []
                temps = []

            curr_date = field.date
            outdir_ = outdir / curr_date.isoformat()

        if field.name == "2t":
            temps.append(field)

        outfields.append(field)

    if len(outfields) > 0:
        print(f"Saving {len(outfields)} fields for time = {curr_date}")
        write_fields(outfields, outdir_, temps, domain, member)


def download_from_lumi(
    domain: Domain, year: int, dst: Path, pattern: str | None, ncpus: int
) -> Path:
    src = f"prod-inference/{domain}/grib/{year}"
    print(f"Downloading from LUMI: {src}")

    cmd = [
        "rclone",
        "copy",
        f"lumi:465002917:{src}",
        f"{dst}",
        "--checkers",
        f"{ncpus}",
        "--transfers",
        f"{ncpus}",
        "--progress",
        "--stats-one-line",
        "--stats-log-level",
        "NOTICE",
        "--stats",
        "10s",
    ]

    if pattern is not None:
        print(f"Using include pattern: {pattern}")
        include = ["--include", f'"{pattern}"']
    else:
        include = []

    log = f"$CAERRA_LOGS/lumi-arhive-{domain}-{year}.log"
    cmd.extend(include + [">>", log])

    subprocess.run(" ".join(cmd), check=True, shell=True)
    return dst


def archive(domain: Domain, member: str, target: Path, log: str):
    cmd = ("../../scripts/mars/archive.sh", f"{target}", f"{domain}", member, ">>", log)
    result = subprocess.run(" ".join(cmd), shell=True, check=False, capture_output=True)

    if result.returncode != 0:
        print(f"Archiving failed: check {log}", file=sys.stderr)
        sys.exit(1)


# actual pattern .../domain/grib/YYYY/YYYY-mm_nXX.grib2
PATTERN = re.compile(r"\d+-\d+_n(\d+).grib2")


def parse_filename(file: Path) -> str:
    match = PATTERN.match(file.name)
    if match is None:
        raise ValueError("Invalid file name:", file)

    member = match.group(1)
    return f"{member:02}"


def process(file: Path, domain: Domain, outdir: Path, archive_only: bool):
    print(f"Processing file {file}")
    member = parse_filename(file)

    outdir /= file.with_suffix("").name
    if not archive_only:
        split_by_day(domain, member, file, outdir)

    for target in outdir.iterdir():
        print(f"Archiving {target} ({member=})")
        log = f"$CAERRA_LOGS/lumi-download-{domain}-{outdir.name}.log"
        # TODO: should use multiprocessing? And do it inside split file?
        archive(domain, member, target, log)


# 1) download 1 year (by month/member)
# 2) split month into days
# 3) archive by day/domain/member
# 4) delete year
# NOTE: 1 year = 12 months * 11 members = 132 files
@click.command()
@click.argument("year", type=int, help="")
@click.argument("domain", type=Domain, help="")
@click.option("--download/--no-download", default=True, help="")
@click.option("--include", type=str, default=None, help="")
@click.option("--workers", type=int, default=None, help="Pool workers")
@click.option("--archive-only", is_flag=True, default=False, help="")
def main(
    domain: Domain,
    year: int,
    download: bool,
    archive_only: bool,
    include: str | None,
    workers: int | None,
):
    lumi = Path(os.path.expandvars("$SCRATCH/lumi"))
    dst = lumi / domain / str(year)
    ncpus = len(os.sched_getaffinity(0))

    if download:
        download_from_lumi(domain, year, dst, include, ncpus)
    else:
        print("Skipping download from LUMI")

    if workers is None:
        workers = ncpus

    outdir = lumi / domain / "outputs"
    with mp.Pool(workers) as pool:
        pool.map(
            functools.partial(
                process,
                domain=domain,
                outdir=outdir,
                archive_only=archive_only,
            ),
            dst.iterdir(),
        )
