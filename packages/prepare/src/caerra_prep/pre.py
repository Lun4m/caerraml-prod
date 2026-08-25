import os
import re
import subprocess
from pathlib import Path

from .main import Args, Domain


class PreProcessor:
    def __init__(self, debug: bool = False):
        self.debug = debug

        default = Path("")
        self.masks = default if debug else Path(os.environ["HOME"]) / "masks"
        self.outputs = default if debug else Path(os.environ["SCRATCH"]) / "datasets"
        self.recipes = default if debug else Path.cwd() / "recipes"

    def prepare_datasets(self, args: Args):
        # recipe names
        ERA5 = "era5t"
        REGRID = "regrid"

        # NOTE: ERA5 needs to be the first one, because the other datasets are
        # cropped versions of ERA5
        inputs = [(ERA5, ERA5)] + [(REGRID, domain) for domain in Domain]

        for recipe_name, domain in inputs:
            recipe = (self.recipes / recipe_name).with_suffix(".yaml")
            self._update_recipe(recipe, domain, args)

            if not self.debug:
                self._create_dataset(recipe, domain)

    def _update_recipe(self, recipe: Path, domain: str, args: Args):
        text = recipe.read_text()

        # Update dates
        text = re.sub(r"(start:\s).*", rf"\g<1>{args.start}", text)
        text = re.sub(r"(end:\s).*", rf"\g<1>{args.end}", text)

        # Update mask file
        mask_path = self.masks / f"{domain}.npz"
        text = re.sub(r"(mask:\s).*", rf"\g<1>{mask_path}", text)

        recipe.write_text(text)

    def _create_dataset(self, recipe: Path, domain: str):
        assert not self.debug

        output = self.outputs / f"{domain}.zarr"

        subprocess.run(
            f"uv run --frozen anemoi-datasets create {recipe} {output} --overwrite",
            check=True,
            shell=True,
        )
