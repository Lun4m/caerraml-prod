import enum
import functools
import os
import re
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import click

# recipe names
ERA5 = "era5t"
REGRID = "regrid"

# Env var names
MASKS_PATH = "CAERRA_MASKS_PATH"
DATASETS_PATH = "CAERRA_DATASETS_PATH"

N_MEMBERS = 11


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
    def __init__(self, date: str, start: str, end: str):
        self.str = date
        self.start = start
        self.end = end


class PreProcessor:
    def __init__(
        self,
        date: Date,
        overwrite: bool,
    ):
        self.date = date

        self.masks = Path(os.environ.get(MASKS_PATH, ""))
        self.dsets = Path(os.environ.get(DATASETS_PATH, ""))
        # recipes dir lives in the root of the repo
        self.recipes = get_recipes_path(__file__, "../../../../recipes")

        # Append date
        self.dsets /= date.str
        self.overwrite = overwrite

    def prepare_datasets(self):
        # NOTE: ERA5 needs to be the first one, because the other datasets are
        # cropped versions of ERA5
        inputs = [(ERA5, ERA5)] + [(REGRID, domain) for domain in Domain]

        for recipe_name, domain in inputs:
            recipe = self.recipes / f"{recipe_name}.template"
            text = self._update_recipe_text(recipe, domain)

            # Create output recipe
            recipe = recipe.with_suffix(".yaml")
            recipe.write_text(text)
            self._create_dataset(recipe, domain)

    def _update_recipe_text(self, recipe: Path, domain: str) -> str:
        text = recipe.read_text()

        # Update dates
        text = re.sub(r"(start:\s).*", rf"\g<1>{self.date.start}", text)
        text = re.sub(r"(end:\s).*", rf"\g<1>{self.date.end}", text)

        # Update mask file
        mask_path = self.masks / f"{domain}.npz"
        text = re.sub(r"(mask:\s).*", rf"\g<1>{mask_path}", text)

        # Update input directory based on day
        era5_path = self.dsets / f"{ERA5}.zarr"
        text = re.sub(r"(\s+dataset:\s).*", rf"\g<1>{era5_path}", text)
        return text

    def _create_dataset(self, recipe: Path, domain: str):
        output = self.dsets / f"{domain}.zarr"
        overwrite = "--overwrite" if self.overwrite else ""

        subprocess.run(
            f"uv run --frozen anemoi-datasets create {recipe} {output} {overwrite}",
            check=True,
            shell=True,
        )


def process_date(value: str | None, lookback: int) -> Date:
    try:
        if value is not None:
            date = datetime.fromisoformat(value)
        else:
            date = datetime.now(UTC) - timedelta(days=lookback)
    except ValueError:
        raise click.BadParameter(
            f"requires a valid ISO 8601 format ('YYYY-mm-dd', 'YYYYmmdd'), got '{value}'"
        )

    date_str = date.strftime("%Y-%m-%d")
    start = date.isoformat(timespec="seconds")

    # anemoi-datasets treats end as inclusive, anemoi-inference as exclusive
    # This should work for both
    end = date + timedelta(hours=23)
    end = end.isoformat(timespec="seconds")
    return Date(date_str, start, end)


def validate_and_process_date(
    ctx: click.Context, _param: click.Option, value: str | None
) -> Date:
    return process_date(value, ctx.params["lookback"])


def common_cli_params(func):
    # NOTE: needs to be defined before 'date' to be available in the callback
    @click.option(
        "--lookback",
        default=7,
        help="Sets the inference run date to 'lookback' days ago. Only used when --date is not set.",
    )
    @click.option(
        "--date",
        default=None,
        callback=validate_and_process_date,
        help="ISO 8601 formatted string of the date for which to run the inference. [default: current day]",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@click.command(context_settings={"show_default": True})
@click.option("--overwrite", is_flag=True)
@common_cli_params
def cli(*args, **kwargs):
    processor = PreProcessor(*args, **kwargs)
    processor.prepare_datasets()
