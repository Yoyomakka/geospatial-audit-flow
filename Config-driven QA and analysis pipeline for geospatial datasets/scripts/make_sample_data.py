"""Generate synthetic example and test geospatial datasets."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point, Polygon, box


def main() -> None:
    """Write small, fictional datasets used by examples and tests."""
    root = Path(__file__).resolve().parents[1]
    example_data_dir = root / "examples" / "urban_green_space_demo" / "data"
    fixture_dir = root / "tests" / "fixtures"
    example_data_dir.mkdir(parents=True, exist_ok=True)
    fixture_dir.mkdir(parents=True, exist_ok=True)

    write_example_data(example_data_dir)
    write_test_fixtures(fixture_dir)
    print(f"Wrote sample data to {example_data_dir.relative_to(root).as_posix()}")
    print(f"Wrote test fixtures to {fixture_dir.relative_to(root).as_posix()}")


def write_example_data(output_dir: Path) -> None:
    """Create fictional district and park polygons."""
    districts = gpd.GeoDataFrame(
        {
            "district_name": ["Northbank", "East Market", "South Gardens", "West Hill"],
            "district_code": ["NB", "EM", "SG", "WH"],
            "geometry": [
                box(-0.14, 51.50, -0.10, 51.54),
                box(-0.10, 51.50, -0.06, 51.54),
                box(-0.10, 51.46, -0.06, 51.50),
                box(-0.14, 51.46, -0.10, 51.50),
            ],
        },
        crs="EPSG:4326",
    )
    districts.to_file(output_dir / "districts.geojson", driver="GeoJSON")

    parks = gpd.GeoDataFrame(
        {
            "name": [
                "Willow Square",
                "Canal Pocket Park",
                "Market Green",
                "Foundry Fields",
                "Southgate Meadow",
                "Hilltop Common",
                "Library Garden",
                "Riverside Play Lot",
            ],
            "park_type": [
                "neighborhood",
                "pocket",
                "civic",
                "sports",
                "natural",
                "common",
                None,
                "playground",
            ],
            "district_hint": ["NB", "NB", "EM", "EM", "SG", "WH", "SG", "NB"],
            "geometry": [
                box(-0.134, 51.512, -0.126, 51.520),
                box(-0.120, 51.526, -0.116, 51.531),
                box(-0.091, 51.512, -0.083, 51.520),
                box(-0.078, 51.523, -0.069, 51.533),
                box(-0.092, 51.472, -0.081, 51.484),
                box(-0.132, 51.470, -0.119, 51.485),
                box(-0.074, 51.490, -0.069, 51.496),
                box(-0.111, 51.505, -0.106, 51.512),
            ],
        },
        crs="EPSG:4326",
    )
    parks.to_file(output_dir / "parks.geojson", driver="GeoJSON")


def write_test_fixtures(output_dir: Path) -> None:
    """Create tiny fixture files for the test suite."""
    points = gpd.GeoDataFrame(
        {"name": ["A", "B", "C"], "value": [1, 2, 3]},
        geometry=[Point(0, 0), Point(1, 1), Point(2, 2)],
        crs="EPSG:4326",
    )
    points.to_file(output_dir / "valid_points.geojson", driver="GeoJSON")

    invalid_polygon = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])
    invalid = gpd.GeoDataFrame(
        {"name": ["bowtie"]},
        geometry=[invalid_polygon],
        crs="EPSG:4326",
    )
    invalid.to_file(output_dir / "invalid_polygon.geojson", driver="GeoJSON")

    missing_values = gpd.GeoDataFrame(
        {
            "name": ["A", None, None, None, "E"],
            "category": ["x", "x", None, None, None],
        },
        geometry=[Point(0, 0), Point(1, 1), Point(2, 2), Point(3, 3), Point(4, 4)],
        crs="EPSG:4326",
    )
    missing_values.to_file(output_dir / "missing_values.geojson", driver="GeoJSON")


if __name__ == "__main__":
    main()
