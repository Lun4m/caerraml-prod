import os
import re
import subprocess
from pathlib import Path

import click

from .utils import Date, Domain, common_cli_params

# recipe names
ERA5 = "era5t"
REGRID = "regrid"

# Env var names
MASKS_PATH = "CAERRA_MASKS_PATH"
DATASETS_PATH = "CAERRA_DATASETS_PATH"


class Paths:
    def __init__(self, date: Date, masks: Path, dsets: Path):
        self.masks = masks

        # Append date to output path and create directory
        self.dsets = dsets / date.str
        self.dsets.mkdir(exist_ok=True)

        # recipes dir lives in the root of the repo
        self.recipes = get_recipes_path(__file__, "../../../../recipes")


def get_recipes_path(file: str, target: str) -> Path:
    """
    file:   path to the file calling this function (i.e., __file__)
    target: relative path to the recipes directory from 'file' parent directory
    """
    base = Path(file).parent
    return (base / target).resolve()


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
def prepare_datasets(date: Date, paths: Paths, overwrite: bool):
    # NOTE: ERA5 needs to be the first one, because the other datasets are
    # cropped versions of ERA5
    inputs = [(ERA5, ERA5)] + [(REGRID, domain) for domain in Domain]

    for recipe_name, domain in inputs:
        recipe = paths.recipes / f"{recipe_name}.template"
        content = update_recipe_content(recipe, domain, date, paths)

        # Create output recipe
        recipe = paths.dsets / f"{domain}.yaml"
        recipe.write_text(content)
        create_dataset(recipe, overwrite)


@click.command(context_settings={"show_default": True})
@click.option("--overwrite", is_flag=True)
@common_cli_params
def cli(date: Date, overwrite: bool):
    masks = Path(os.environ.get(MASKS_PATH, ""))
    dsets = Path(os.environ.get(DATASETS_PATH, ""))
    paths = Paths(date, masks, dsets)
    prepare_datasets(date, paths, overwrite)
