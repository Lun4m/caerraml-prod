import os
import re
import subprocess
from pathlib import Path

from .cli import Args, Domain


class PreProcessor:
    YAML = ".yaml"
    ZARR = ".zarr"
    NPZ = ".npz"

    def __init__(self):
        perm = Path(os.environ["PERM"])
        self.recipes = perm / "recipes"
        self.masks = perm / "masks"

        self.outputs = Path(os.environ["SCRATCH"]) / "outputs"

    def prepare_datasets(self, args: Args):
        # recipe names
        ERA5 = "era5t"
        REGRID = "regrid"

        # NOTE: ERA5 needs to be the first one, because the other datasets are
        # cropped versions of ERA5
        inputs = [(ERA5, ERA5)] + [(REGRID, domain) for domain in Domain]

        for recipe_name, domain in inputs:
            recipe = (self.recipes / recipe_name).with_suffix(self.YAML)
            self.update_recipe(recipe, domain, args)
            self.create_dataset(recipe, domain)

    def update_recipe(self, recipe: Path, domain: str, args: Args):
        text = recipe.read_text()

        # Update dates
        text = re.sub(r"(start:\s).+", rf"\1{args.start}", text)
        text = re.sub(r"(end:\s).+", rf"\1{args.end}", text)

        # Update mask file
        mask_path = (self.masks / domain).with_suffix(self.NPZ)
        text = re.sub(r"(mask:\s).+", rf"\1{mask_path}", text)

        recipe.write_text(text)

    def create_dataset(self, recipe: Path, domain: str):
        output = (self.outputs / domain).with_suffix(self.ZARR)

        subprocess.run(
            f"uv run --frozen anemoi-datasets create {recipe} {output}",
            check=True,
            shell=True,
        )


def main():
    args = Args.parse()

    processor = PreProcessor()
    processor.prepare_datasets(args)


if __name__ == "__main__":
    main()
