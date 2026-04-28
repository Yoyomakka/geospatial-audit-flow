from __future__ import annotations

import geopandas as gpd
from shapely.geometry import Point, Polygon

from geoaudit.checks import (
    check_bbox,
    check_crs,
    check_duplicate_geometry,
    check_empty_geometry,
    check_geometry_types,
    check_invalid_geometry,
    check_missing_values,
    run_checks,
)


def test_crs_check_passes_when_crs_exists() -> None:
    gdf = gpd.GeoDataFrame({"name": ["A"]}, geometry=[Point(0, 0)], crs="EPSG:4326")

    result = check_crs(gdf)

    assert result.status == "PASS"


def test_empty_geometry_check_warns_for_some_empty() -> None:
    gdf = gpd.GeoDataFrame({"name": ["A", "B"]}, geometry=[Point(0, 0), None], crs="EPSG:4326")

    result = check_empty_geometry(gdf)

    assert result.status == "WARN"
    assert result.value == {"empty_count": 1, "row_count": 2}


def test_invalid_geometry_check_warns_for_bowtie_polygon() -> None:
    bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])
    gdf = gpd.GeoDataFrame({"name": ["bad"]}, geometry=[bowtie], crs="EPSG:4326")

    result = check_invalid_geometry(gdf)

    assert result.status == "WARN"
    assert result.value == {"invalid_count": 1, "row_count": 1}


def test_duplicate_geometry_check_warns() -> None:
    gdf = gpd.GeoDataFrame(
        {"name": ["A", "B", "C"]},
        geometry=[Point(0, 0), Point(0, 0), Point(1, 1)],
        crs="EPSG:4326",
    )

    result = check_duplicate_geometry(gdf)

    assert result.status == "WARN"
    assert result.value == {"duplicate_geometry_count": 2}


def test_missing_values_warns_for_high_missing_ratio() -> None:
    gdf = gpd.GeoDataFrame(
        {"name": ["A", None, None], "kind": ["x", "y", "z"]},
        geometry=[Point(0, 0), Point(1, 1), Point(2, 2)],
        crs="EPSG:4326",
    )

    result = check_missing_values(gdf)

    assert result.status == "WARN"
    assert result.value is not None
    assert result.value["name"] > 0.4


def test_geometry_types_warns_for_mixed_types() -> None:
    gdf = gpd.GeoDataFrame(
        {"name": ["point", "line"]},
        geometry=[Point(0, 0), Point(1, 1).buffer(1)],
        crs="EPSG:4326",
    )

    result = check_geometry_types(gdf)

    assert result.status == "WARN"


def test_bbox_warns_for_bad_epsg4326_bounds() -> None:
    gdf = gpd.GeoDataFrame({"name": ["bad"]}, geometry=[Point(200, 95)], crs="EPSG:4326")

    result = check_bbox(gdf)

    assert result.status == "WARN"


def test_run_checks_respects_config() -> None:
    gdf = gpd.GeoDataFrame({"name": ["A"]}, geometry=[Point(0, 0)], crs="EPSG:4326")
    config = {"checks": {"crs": True, "bbox": True, "missing_values": False}}

    results = run_checks(gdf, config)

    assert [result.name for result in results] == ["crs", "bbox"]
