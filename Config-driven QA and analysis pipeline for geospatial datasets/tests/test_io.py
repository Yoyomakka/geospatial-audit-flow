from __future__ import annotations

from pathlib import Path

from geoaudit.io import read_geodata, write_geodata


def test_read_geojson_fixture() -> None:
    gdf = read_geodata(Path("tests/fixtures/valid_points.geojson"))

    assert len(gdf) == 3
    assert gdf.crs is not None
    assert gdf.crs.to_epsg() == 4326


def test_write_geojson(tmp_path: Path) -> None:
    gdf = read_geodata(Path("tests/fixtures/valid_points.geojson"))
    output_path = tmp_path / "points.geojson"

    write_geodata(gdf, output_path)
    reread = read_geodata(output_path)

    assert output_path.exists()
    assert len(reread) == 3
