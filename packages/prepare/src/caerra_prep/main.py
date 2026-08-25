import enum
import os
import re
import subprocess
from argparse import ArgumentParser, ArgumentTypeError
from datetime import datetime, timedelta
from pathlib import Path
from typing import Self

N_MEMBERS = 11


class Domain(enum.StrEnum):
    CARRA_EAST = "carra-east"
    CARRA_WEST = "carra-west"
    CERRA = "cerra"

    def __repr__(self):
        return self.value


class Args:
    def __init__(
        self,
        date: datetime,
        members: int = N_MEMBERS,
        debug: bool = False,
    ):
        self.debug = debug
        self.start = date.isoformat(timespec="seconds")

        # anemoi-datasets treats end as inclusive, anemoi-inference as exclusive
        # This should work for both
        end = date + timedelta(hours=23)
        self.end = end.isoformat(timespec="seconds")
        self.members = members

    @staticmethod
    def validate_date(arg: str) -> datetime:
        try:
            date = datetime.fromisoformat(arg)
            assert date.hour == 0 and date.minute == 0 and date.second == 0, ValueError
        except ValueError:
            raise ArgumentTypeError(f"requires format 'YYYY-mm-dd', got '{arg}'")
        return date

    @classmethod
    def parse(cls) -> Self:
        ap = ArgumentParser()
        ap.add_argument(
            "date",
            help="Date for which to run the inference (format 'YYYY-mm-dd')",
            type=cls.validate_date,
        )
        ap.add_argument(
            "--members",
            help="Number of members",
            type=int,
            default=N_MEMBERS,
        )
        ap.add_argument("--debug", action="store_true")

        args = ap.parse_args()
        return cls(**vars(args))


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


def main():
    args = Args.parse()

    processor = PreProcessor(args.debug)
    processor.prepare_datasets(args)
