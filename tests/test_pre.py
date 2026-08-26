from pathlib import Path

from caerra_prep import Args, PreProcessor


def test_update_recipe(tmp_path: Path):
    date = "2026-01-01"
    path = Path("okay")
    domain = "whatever"
    args = Args(Args.validate_date(date))

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
    dataset: {path / date / "era5t.zarr"}
    mask: {path / domain}.npz
"""
    tmp_file = tmp_path / "tmp.yaml"
    tmp_file.write_text(content)

    proc = PreProcessor(args, masks=path, dsets=path, recipes=path)
    proc._update_recipe(tmp_file, domain, args)

    updated = tmp_file.read_text()
    assert updated == expected
