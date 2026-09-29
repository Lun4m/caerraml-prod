import enum
import functools
import os
import re
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from subprocess import CalledProcessError

import click

# recipe names
ERA5 = "era5t"
REGRID = "regrid"

# Env var names
MASKS_PATH = "CAERRA_MASKS_PATH"
DATASETS_PATH = "CAERRA_DATASETS_PATH"

N_MEMBERS = 11
DEFAULT_LOOKBACK = 8  # days


def get_recipes_path(file: str, target: str) -> Path:
    """
    file:   path to the file calling this function (i.e., __file__)
    target: relative path to the recipes directory from 'file' parent directory
    """
    base = Path(file).parent
    return (base / target).resolve()


class Domain(enum.StrEnum):
    CARRA_EAST = "carra-east"
    CARRA_WEST = "carra-west"
    CERRA = "cerra"

    def __repr__(self):
        return self.value


class Date:
    def __init__(self, date: datetime):
        date_str = date.strftime("%Y-%m-%d")
        start = date.isoformat(timespec="seconds")

        # anemoi-datasets treats end as inclusive, anemoi-inference as exclusive
        # This should work for both
        end = date + timedelta(hours=23)
        end = end.isoformat(timespec="seconds")

        self.str = date_str
        self.start = start
        self.end = end


class Paths:
    def __init__(self, date: Date, masks: Path, dsets: Path, overwrite: bool):
        self.masks = masks

        # Append date to output path and create directory
        self.dsets = dsets / date.str
        self.dsets.mkdir(exist_ok=True)

        # recipes dir lives in the root of the repo
        self.recipes = get_recipes_path(__file__, "../../../../recipes")

        self.overwrite = overwrite


def send_email_on_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except CalledProcessError as e:
            # TODO: send email on error?
            pass


def update_recipe_content(recipe: Path, domain: str, date: Date, paths: Paths) -> str:
    text = recipe.read_text()

    # Update dates
    text = re.sub(r"(start:\s).*", rf"\g<1>{date.start}", text)
    text = re.sub(r"(end:\s).*", rf"\g<1>{date.end}", text)

    # Update mask file
    mask_path = paths.masks / f"{domain}.npz"
    text = re.sub(r"(mask:\s).*", rf"\g<1>{mask_path}", text)

    # Update input directory based on day
    era5_path = paths.dsets / f"{ERA5}.zarr"
    text = re.sub(r"(\s+dataset:\s).*", rf"\g<1>{era5_path}", text)
    return text


def create_dataset(recipe: Path, overwrite: bool):
    # Create output dataset
    output = recipe.with_suffix(".zarr")

    if output.exists() and not overwrite:
        print(f"Skipping {output} because it already exists.")
        return

    over = "--overwrite" if overwrite else ""
    subprocess.run(
        f"uv run --frozen anemoi-datasets create {recipe} {output} {over}",
        check=True,
        shell=True,
    )


# TODO: the logic here if datasets/recipes already exist is a bit inconsistent
def prepare_datasets(date: Date, paths: Paths):
    # NOTE: ERA5 needs to be the first one, because the other datasets are
    # cropped versions of ERA5
    inputs = [(ERA5, ERA5)] + [(REGRID, domain) for domain in Domain]

    for recipe_name, domain in inputs:
        recipe = paths.recipes / f"{recipe_name}.template"
        content = update_recipe_content(recipe, domain, date, paths)

        # Create output recipe
        recipe = paths.dsets / f"{domain}.yaml"
        recipe.write_text(content)
        create_dataset(recipe, paths.overwrite)


def validate_date(value: str | None, lookback: int = DEFAULT_LOOKBACK) -> Date:
    try:
        if value is None:
            date = datetime.now(UTC) - timedelta(days=lookback)
        else:
            date = datetime.fromisoformat(value)
    except ValueError:
        raise click.BadParameter(
            f"requires a valid ISO 8601 format ('YYYY-mm-dd', 'YYYYmmdd'), got '{value}'"
        )

    date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    return Date(date)


def common_cli_params(func):
    # NOTE: needs to be defined before 'date' to be available in the callback
    @click.option(
        "--lookback",
        default=DEFAULT_LOOKBACK,
        help="Sets the inference run date to 'lookback' days ago. Only used when --date is not set.",
    )
    @click.option(
        "--date",
        "date_cli",
        default=None,
        help="ISO 8601 formatted string of the date for which to run the inference. [default: current day]",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@click.command(context_settings={"show_default": True})
@click.option("--overwrite", is_flag=True)
@common_cli_params
def cli(date_cli: str | None, lookback: int, overwrite: bool):
    date = validate_date(date_cli, lookback)
    masks = Path(os.environ.get(MASKS_PATH, ""))
    dsets = Path(os.environ.get(DATASETS_PATH, ""))
    paths = Paths(date, masks, dsets, overwrite)
    prepare_datasets(date, paths)
