"""Common geospatial data fixes."""

from __future__ import annotations

from typing import Any

import geopandas as gpd
from shapely.geometry.base import BaseGeometry


def drop_empty_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Drop rows with null or empty geometries."""
    before = len(gdf)
    cleaned = gdf.loc[~(gdf.geometry.isna() | gdf.geometry.is_empty)].copy()
    cleaned.attrs["geoaudit_dropped_empty_geometry_count"] = before - len(cleaned)
    return cleaned


def repair_invalid_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Repair invalid geometries using make_valid, falling back to buffer(0)."""
    repaired = gdf.copy()
    invalid_mask = (
        repaired.geometry.notna()
        & ~repaired.geometry.is_empty
        & ~repaired.geometry.is_valid
    )
    repaired_count = int(invalid_mask.sum())

    if repaired_count == 0:
        repaired.attrs["geoaudit_repaired_geometry_count"] = 0
        return repaired

    geometry_column = repaired.geometry.name
    repaired.loc[invalid_mask, geometry_column] = repaired.loc[
        invalid_mask,
        geometry_column,
    ].apply(_make_valid_geometry)
    repaired.attrs["geoaudit_repaired_geometry_count"] = repaired_count
    return repaired


def reproject(gdf: gpd.GeoDataFrame, target_crs: str) -> gpd.GeoDataFrame:
    """Reproject a GeoDataFrame to a target CRS."""
    if gdf.crs is None:
        raise ValueError("Cannot reproject data without a source CRS.")
    return gdf.to_crs(target_crs)


def apply_fixes(gdf: gpd.GeoDataFrame, config: dict[str, Any]) -> gpd.GeoDataFrame:
    """Apply configured fixes in a predictable order."""
    fixes_config = config.get("fixes", {})
    if not isinstance(fixes_config, dict) or not bool(fixes_config.get("enabled", False)):
        return gdf.copy()

    cleaned = gdf.copy()
    if bool(fixes_config.get("drop_empty_geometry", False)):
        cleaned = drop_empty_geometry(cleaned)

    if bool(fixes_config.get("repair_geometry", False)):
        cleaned = repair_invalid_geometry(cleaned)

    target_crs = fixes_config.get("target_crs")
    if target_crs:
        cleaned = reproject(cleaned, str(target_crs))

    return cleaned


def _make_valid_geometry(geometry: BaseGeometry) -> BaseGeometry:
    try:
        from shapely import make_valid

        repaired = make_valid(geometry)
    except Exception:
        repaired = geometry.buffer(0)

    if repaired is None or repaired.is_empty:
        return geometry
    return repaired
