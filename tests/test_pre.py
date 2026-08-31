from pathlib import Path

from caerra_prep import Args, PreProcessor

# root of the repository
ROOT = Path(__file__).parent.parent.resolve()
RECIPES = ROOT / "recipes"


def test_update_recipe(tmp_path: Path):
    tmp_file = tmp_path / "tmp.template"

    date = "2026-01-01"
    dt = Args.validate_date(date)
    args = Args(date=dt)
    domain = "whatever"

    content = """dates:
    frequency: 3h
    start: asdasd
    end: sdfsdf

    regrid:
        dataset: my_precious/path.out.zarr
        mask: sdfsdfsdfsdf
    """

    expected = f"""dates:
    frequency: 3h
    start: {date}T00:00:00
    end: {date}T23:00:00

    regrid:
        dataset: {Path(date) / "era5t.zarr"}
        mask: {domain}.npz
    """

    tmp_file.write_text(content)

    proc = PreProcessor(args)
    assert proc.recipes == RECIPES

    out = proc._update_recipe_text(tmp_file, domain, args)
    assert out == expected
