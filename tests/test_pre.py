from pathlib import Path

from caerra_prep import Paths
from caerra_prep.main import Date, get_recipes_path, update_recipe_text, validate_date


def test_update_recipe(tmp_path: Path):
    tmp_file = tmp_path / "tmp.template"

    dt = validate_date("2026-01-01")
    date = Date(dt)

    domain = "whatever"
    masks = Path("")
    dsets = masks

    content = """dates:
    frequency: 3h
    start: asdasd
    end: sdfsdf

    input:
      pipe:
        anemoi-dataset:
          dataset: __GENERATED__
        regrid:
          mask: __GENERATED__
    """

    expected = """dates:
    frequency: 3h
    start: 2026-01-01T00:00:00
    end: 2026-01-01T23:00:00

    input:
      pipe:
        anemoi-dataset:
          dataset: 2026-01-01/era5t.zarr
        regrid:
          mask: whatever.npz
    """

    tmp_file.write_text(content)

    paths = Paths(date, masks, dsets, overwrite=False)
    assert paths.recipes == get_recipes_path(__file__, "../recipes")

    out = update_recipe_text(tmp_file, domain, date, paths)
    assert out == expected
