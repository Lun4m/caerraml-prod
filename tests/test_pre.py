from pathlib import Path

from caerra_prep import PreProcessor
from caerra_prep.main import get_recipes_path, process_date


def test_update_recipe(tmp_path: Path):
    tmp_file = tmp_path / "tmp.template"

    date = process_date("2026-01-01", 0)
    domain = "whatever"

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

    expected = f"""dates:
    frequency: 3h
    start: {date.str}T00:00:00
    end: {date.str}T23:00:00

    input:
      pipe:
        anemoi-dataset:
          dataset: {Path(date.str) / "era5t.zarr"}
        regrid:
          mask: {domain}.npz
    """

    tmp_file.write_text(content)

    proc = PreProcessor(date, overwrite=False)
    assert proc.recipes == get_recipes_path(__file__, "../recipes")

    out = proc._update_recipe_text(tmp_file, domain)
    assert out == expected
