import os
import sys
from pathlib import Path

import click
import earthkit.data as ekd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from caerra_utils.prepare import Date, common_cli_params


class Range:
    def __init__(self, min: float, max: float):
        self.min = min
        self.max = max


# Define reasonable thresholds for parameters
THRESHOLDS = {
    "ws": Range(0.0, 100.0),
    "2t": Range(-100.0, 400.0),
    "mn2t": Range(-100.0, 400.0),
    "mx2t": Range(-100.0, 400.0),
    "2r": Range(0.0, 100.0),
    "tcc": Range(0.0, 100.0),
    # Add other parameters and their physical bounds as needed
}


def get_field(filename: str, keys: dict[str, str]) -> tuple[np.ndarray, str]:
    if filename.endswith(("grib", "grib2")):
        # NOTE: used for testing, not present in grib messages
        _ = keys.pop("database", None)

        fields = ekd.from_source("file", filename).to_fieldlist()
        fields = fields.sel({f"metadata.{k}": v for k, v in keys.items()})
    elif len(filename.split(".")) != 1:
        raise ValueError(f"Unexpected filename extension: {filename}")
    else:
        request = {
            "origin": filename,
            "expver": "prod",
            "class": "rr",
            "date": keys["date"],
            "time": keys["time"],
            "param": keys["param"],
            "type": keys.get("type", "an"),
            "step": keys.get("step", "0"),
            "stream": keys.get("stream", "oper"),
            "levtype": keys.get("levtype", "sfc"),
            "database": keys.get("database"),
            "number": keys.get("number"),
        }

        fields = ekd.from_source("mars", request=request).to_fieldlist()

    assert len(fields) == 1
    field: ekd.Field = fields[0]

    name, mask = field.metadata(("name", "missingValue"))
    val = np.ma.masked_values(field.to_numpy(), mask)
    return val, name


def str_to_dict(value: str | None) -> dict[str, str] | None:
    if value is None:
        return None

    try:
        return dict(v.split("=") for v in value.split(","))
    except ValueError:
        raise click.BadParameter(
            f"Expected comma separated list of key value pairs (key1=val1,key2=val2). Got: {value}"
        )


@click.group()
def cli():
    pass


@cli.command(
    context_settings={"show_default": True},
    short_help="Take a quicklook on parameter from a grib file",
    help="""
Take a quick look at the fields in a grib file or in the MARS archive.

Examples:
  1) Single grib file
  caerra-monitor quicklook input.grib2 -w param=2t,date=2020-01-01,time=00

  2) Plot data fetched from MARS
  caerra-monitor quicklook no-ar-pa -w param=2t,date=2020-12-17,hour=06,step=3,type=fc

  2) Diff MARS and grib file
  caerra-monitor quicklook no-ar-ce -w param=2t,date=2020-12-17,hour=06,step=0 --diff input.grib2
 """,
)
@click.argument("filename", type=str, help="grib filename (or mars origin)")
@click.option(
    "-o",
    "--output",
    type=str,
    help="output image file",
)
@click.option(
    "-w",
    "--where",
    required=True,
    callback=lambda _ctx, _param, val: str_to_dict(val),
    help="Comma separated list of metadata key specifiers",
)
@click.option("--diff", type=str, default=None, help="name of file to compare")
@click.option(
    "-dw",
    "--diff-where",
    callback=lambda _ctx, _param, val: str_to_dict(val),
    help="Second list of metadata key specifiers, used to diff against the first one",
)
@click.option("--min", "vmin", type=float, default=None, help="min")
@click.option("--max", "vmax", type=float, default=None, help="max")
@click.option("--cmap", default="jet", help="Color map used for plotting")
def quicklook(
    filename: str,
    output: str | None,
    where: dict[str, str],
    diff: str | None,
    diff_where: dict[str, str] | None,
    vmin: float | None,
    vmax: float | None,
    cmap: str,
):
    field, name = get_field(filename, where)

    if diff or diff_where:
        filename = diff if diff else filename
        where = diff_where if diff_where else where
        other, _ = get_field(filename, where)

        field -= other
        lim = np.nanmax(np.abs(field))
        vmin, vmax = -lim, lim
        cmap = "RdBu_r"

    matplotlib.rcParams["image.interpolation"] = "none"
    matplotlib.rcParams["axes.facecolor"] = "lightgrey"

    plt.imshow(field, cmap=cmap, vmin=vmin, vmax=vmax, origin="lower")
    plt.title(name)
    plt.colorbar()

    if output is not None:
        plt.savefig(output, dpi=300)

    plt.show()


@cli.command("check", short_help="Check field ranges in output files")
@click.option(
    "--dir",
    "directory",
    type=Path,
    help="Directory containing output files",
)
@common_cli_params
def check_data_range(date: Date, directory: Path | None):
    if directory is None:
        directory = Path(os.environ["CAERRA_OUTPUTS_PATH"])

    directory /= str(date)

    rc = 0
    for file in directory.glob("*.grib2"):
        print(f"Processing File: {file}")

        fields = ekd.from_source("file", str(file)).to_fieldlist()

        for field in fields:
            param, origin, time = field.get(
                ("metadata.param", "metadata.origin", "metadata.time")
            )

            values = field.values
            v_min = values.min()
            v_max = values.max()

            thresh = THRESHOLDS.get(param)
            if thresh is None:
                continue

            # np.isclose(v_min, thresh.min)

            if v_min < thresh.min:
                rc = 1
                print(
                    f"{origin} {param} {date} {time}: invalid min ({v_min} < {thresh.min})",
                    file=sys.stderr,
                )
            if v_max > thresh.max:
                rc = 1
                print(
                    f"{origin} {param} {date} {time}: invalid max ({v_max} > {thresh.max})",
                    file=sys.stderr,
                )

    sys.exit(rc)
