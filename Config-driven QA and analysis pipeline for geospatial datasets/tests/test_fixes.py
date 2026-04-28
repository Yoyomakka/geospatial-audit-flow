from __future__ import annotations

import geopandas as gpd
from shapely.geometry import Point, Polygon

from geoaudit.fixes import apply_fixes, drop_empty_geometry, repair_invalid_geometry


def test_drop_empty_geometry_removes_null_geometry() -> None:
    gdf = gpd.GeoDataFrame({"name": ["A", "B"]}, geometry=[Point(0, 0), None], crs="EPSG:4326")

    cleaned = drop_empty_geometry(gdf)

    assert len(cleaned) == 1
    assert cleaned.attrs["geoaudit_dropped_empty_geometry_count"] == 1


def test_repair_invalid_geometry_makes_bowtie_valid() -> None:
    bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])
    gdf = gpd.GeoDataFrame({"name": ["bad"]}, geometry=[bowtie], crs="EPSG:4326")

    repaired = repair_invalid_geometry(gdf)

    assert repaired.geometry.is_valid.all()
    assert repaired.attrs["geoaudit_repaired_geometry_count"] == 1


def test_apply_fixes_reprojects_when_configured() -> None:
    gdf = gpd.GeoDataFrame({"name": ["A"]}, geometry=[Point(0, 0)], crs="EPSG:4326")
    config = {
        "fixes": {
            "enabled": True,
            "drop_empty_geometry": True,
            "repair_geometry": True,
            "target_crs": "EPSG:3857",
        }
    }

    cleaned = apply_fixes(gdf, config)

    assert cleaned.crs is not None
    assert cleaned.crs.to_epsg() == 3857
