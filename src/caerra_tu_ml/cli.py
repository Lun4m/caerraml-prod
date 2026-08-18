import enum
from argparse import ArgumentParser, ArgumentTypeError
from datetime import datetime
from typing import Self


class Domain(enum.StrEnum):
    CARRA_EAST = "carra-east"
    CARRA_WEST = "carra-west"
    CERRA = "cerra"

    def __repr__(self):
        return self.value


class Action(enum.StrEnum):
    PREPARE = "prepare"
    RUN = "run"


class Args:
    def __init__(self, action: Action, start: str, end: str):
        self.action = action
        self.start = start
        self.end = end

    @staticmethod
    def validate_date(arg: str) -> str:
        try:
            _ = datetime.fromisoformat(arg)
        except ValueError:
            raise ArgumentTypeError(
                f"requires format 'YYYY-mm-ddTHH-MM-SS', got '{arg}'"
            )
        return arg

    @classmethod
    def parse(cls) -> Self:
        ap = ArgumentParser()
        ap.add_argument("action", type=Action)
        ap.add_argument("start", type=cls.validate_date)
        ap.add_argument("end", type=cls.validate_date)
        args = ap.parse_args()

        return cls(**vars(args))
