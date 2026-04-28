from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, box

from geoaudit.analysis import run_analysis_recipes


def test_area_by_category_writes_grouped_area_csv(tmp_path: Path) -> None:
    gdf = gpd.GeoDataFrame(
        {"park_type": ["pocket", "pocket", "natural"]},
        geometry=[box(0, 0, 0.01, 0.01), box(0.02, 0, 0.03, 0.01), box(0, 0.02, 0.01, 0.03)],
        crs="EPSG:4326",
    )
    output_path = tmp_path / "area.csv"
    config = {
        "__base_dir__": str(tmp_path),
        "fixes": {"target_crs": "EPSG:3857"},
        "analysis": [
            {
                "type": "area_by_category",
                "category_column": "park_type",
                "output": str(output_path),
            }
        ],
    }

    results = run_analysis_recipes(gdf, config)
    output = pd.read_csv(output_path)

    assert results[0].recipe_type == "area_by_category"
    assert set(output["category"]) == {"pocket", "natural"}
    assert output.loc[output["category"] == "pocket", "feature_count"].iloc[0] == 2
    assert output["total_area_sqm"].gt(0).all()


def test_count_by_polygon_writes_counts_csv(tmp_path: Path) -> None:
    gdf = gpd.GeoDataFrame(
        {"name": ["A", "B", "C"]},
        geometry=[Point(0.5, 0.5), Point(1.5, 0.5), Point(3, 3)],
        crs="EPSG:4326",
    )
    polygons = gpd.GeoDataFrame(
        {"district_name": ["west", "east"]},
        geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1)],
        crs="EPSG:4326",
    )
    polygon_path = tmp_path / "polygons.geojson"
    polygons.to_file(polygon_path, driver="GeoJSON")
    output_path = tmp_path / "counts.csv"
    config = {
        "__base_dir__": str(tmp_path),
        "analysis": [
            {
                "type": "count_by_polygon",
                "polygon_path": str(polygon_path),
                "polygon_name_column": "district_name",
                "output": str(output_path),
            }
        ],
    }

    results = run_analysis_recipes(gdf, config)
    output = pd.read_csv(output_path)

    assert results[0].recipe_type == "count_by_polygon"
    assert dict(zip(output["polygon_name"], output["feature_count"], strict=True)) == {
        "west": 1,
        "east": 1,
    }
