import enum
from argparse import ArgumentParser, ArgumentTypeError
from datetime import datetime, timedelta
from typing import Self

from .pre import PreProcessor

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


def main():
    args = Args.parse()

    processor = PreProcessor(args.debug)
    processor.prepare_datasets(args)
