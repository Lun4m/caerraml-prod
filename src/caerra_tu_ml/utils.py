import enum
import functools
import os
from datetime import UTC, datetime, timedelta
from subprocess import CalledProcessError

import click

# recipe names
ERA5 = "era5t"
REGRID = "regrid"

# Env var names
MASKS_PATH = "CAERRA_MASKS_PATH"
DATASETS_PATH = "CAERRA_DATASETS_PATH"


class Domain(enum.StrEnum):
    CARRA_EAST = "carra-east"
    CARRA_WEST = "carra-west"
    CERRA = "cerra"

    def __repr__(self):
        return self.value

    def suite_name(self) -> int:
        match self:
            case Domain.CARRA_EAST:
                return 7
            case Domain.CARRA_WEST:
                return 8
            case Domain.CERRA:
                return 10


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


def get_production_delay() -> int:
    default_delay = 7  # days

    if delay := os.environ.get("CAERRA_PROD_DELAY"):
        return int(delay)

    return default_delay


def validate_date(value: str | None) -> Date:
    try:
        if value is None:
            delay = get_production_delay()
            date = datetime.now(UTC) - timedelta(days=delay)
        else:
            date = datetime.fromisoformat(value)
    except ValueError:
        raise click.BadParameter(
            f"requires a valid ISO 8601 format ('YYYY-mm-dd', 'YYYYmmdd'), got '{value}'"
        )

    date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    return Date(date)


def common_cli_params(func):
    @click.option(
        "--date",
        default=None,
        callback=lambda _ctx, _param, val: validate_date(val),
        help="ISO 8601 formatted string of the date for which to run the inference. [default: current day]",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def send_email_on_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except CalledProcessError as e:
            # TODO: send email on error?
            pass
