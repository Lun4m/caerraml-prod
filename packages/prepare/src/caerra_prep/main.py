import enum
import os
import re
import subprocess
from argparse import ArgumentParser, ArgumentTypeError
from datetime import datetime, timedelta
from pathlib import Path
from typing import Self

# recipe names
ERA5 = "era5t"
REGRID = "regrid"

# Env var names
MASKS_PATH = "CAERRA_MASKS_PATH"
DATASETS_PATH = "CAERRA_DATASETS_PATH"

N_MEMBERS = 11


def get_recipes_path() -> Path:
    """Assumes we are invoking the console scripts from the root of the repository"""
    return Path.cwd() / "recipes"


class Domain(enum.StrEnum):
    CARRA_EAST = "carra-east"
    CARRA_WEST = "carra-west"
    CERRA = "cerra"

    def __repr__(self):
        return self.value


class Args:
    def __init__(
        self,
        date: tuple[str, datetime],
        n_members: int = N_MEMBERS,
        members: list[int] | None = None,
        domains: list[Domain] | None = None,
        overwrite: bool = False,
    ):
        date_str, _date = date
        self.date_str = date_str
        self.start = _date.isoformat(timespec="seconds")

        # anemoi-datasets treats end as inclusive, anemoi-inference as exclusive
        # This should work for both
        end = _date + timedelta(hours=23)
        self.end = end.isoformat(timespec="seconds")

        self.domains = set(domains) if domains is not None else set(Domain)
        self.members = members if members is not None else list(range(n_members))

        self.n_members = n_members
        self.overwrite = overwrite

    @staticmethod
    def validate_date(arg: str) -> tuple[str, datetime]:
        try:
            date = datetime.fromisoformat(arg)
            assert date.hour == 0 and date.minute == 0 and date.second == 0, ValueError
        except ValueError:
            raise ArgumentTypeError(f"requires format 'YYYY-mm-dd', got '{arg}'")
        return (arg, date)

    @classmethod
    def parse(cls) -> Self:
        ap = ArgumentParser()
        ap.add_argument(
            "date",
            help="Date for which to run the inference (format 'YYYY-mm-dd')",
            type=cls.validate_date,
        )
        ap.add_argument(
            "--n_members",
            type=int,
            default=N_MEMBERS,
            help="Number of members",
        )
        ap.add_argument(
            "--domains",
            nargs="+",
            type=Domain,
            choices=Domain,
            default=None,
            help="Only operate on the given domains (all by default)",
        )
        ap.add_argument(
            "--members",
            nargs="+",
            type=int,
            default=None,
            help="Only generate the given members",
        )
        ap.add_argument(
            "--overwrite", help="Whether to overwrite the datasets", action="store_true"
        )

        args = ap.parse_args()
        return cls(**vars(args))


class PreProcessor:
    def __init__(
        self,
        args: Args,
    ):
        self.masks = Path(os.environ.get(MASKS_PATH, ""))
        self.dsets = Path(os.environ.get(DATASETS_PATH, ""))
        self.recipes = get_recipes_path()

        # Append date
        self.dsets /= args.date_str
        self.overwrite = args.overwrite

    def prepare_datasets(self, args: Args):
        # NOTE: ERA5 needs to be the first one, because the other datasets are
        # cropped versions of ERA5
        inputs = [(ERA5, ERA5)] + [(REGRID, domain) for domain in Domain]

        for recipe_name, domain in inputs:
            recipe = self.recipes / f"{recipe_name}.template"
            text = self._update_recipe_text(recipe, domain, args)

            # Create output recipe
            recipe = recipe.with_suffix(".yaml")
            recipe.write_text(text)
            self._create_dataset(recipe, domain)

    def _update_recipe_text(self, recipe: Path, domain: str, args: Args) -> str:
        text = recipe.read_text()

        # Update dates
        text = re.sub(r"(start:\s).*", rf"\g<1>{args.start}", text)
        text = re.sub(r"(end:\s).*", rf"\g<1>{args.end}", text)

        # Update mask file
        mask_path = self.masks / f"{domain}.npz"
        text = re.sub(r"(mask:\s).*", rf"\g<1>{mask_path}", text)

        # Update input directory based on day
        era5_path = self.dsets / f"{ERA5}.zarr"
        text = re.sub(r"(dataset:\s).*", rf"\g<1>{era5_path}", text)
        return text

    def _create_dataset(self, recipe: Path, domain: str):
        output = self.dsets / f"{domain}.zarr"
        overwrite = "--overwrite" if self.overwrite else ""

        subprocess.run(
            f"uv run --frozen anemoi-datasets create {recipe} {output} {overwrite}",
            check=True,
            shell=True,
        )


def main():
    args = Args.parse()

    processor = PreProcessor(args)
    processor.prepare_datasets(args)
