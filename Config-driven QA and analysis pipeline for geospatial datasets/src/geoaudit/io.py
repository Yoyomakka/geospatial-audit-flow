"""Geospatial input and output helpers."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

SUPPORTED_VECTOR_EXTENSIONS = {".geojson", ".json", ".gpkg", ".shp"}
CSV_COORDINATE_PAIRS: tuple[tuple[str, str], ...] = (
    ("lon", "lat"),
    ("longitude", "latitude"),
    ("x", "y"),
)


def read_geodata(
    path: str | Path,
    layer: str | None = None,
    crs: str | None = None,
) -> gpd.GeoDataFrame:
    """Read a geospatial file into a GeoDataFrame."""
    data_path = Path(path).expanduser()
    if not data_path.exists():
        raise ValueError(f"Input dataset does not exist: {data_path}")

    suffix = data_path.suffix.lower()
    if suffix == ".csv":
        return _read_csv_points(data_path, crs)

    if suffix not in SUPPORTED_VECTOR_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_VECTOR_EXTENSIONS | {".csv"}))
        raise ValueError(f"Unsupported input extension '{suffix}'. Supported: {supported}")

    try:
        gdf = gpd.read_file(data_path, layer=layer, engine="pyogrio")
    except TypeError:
        gdf = gpd.read_file(data_path, layer=layer)

    if crs and gdf.crs is None:
        gdf = gdf.set_crs(crs)

    return gdf


def write_geodata(gdf: gpd.GeoDataFrame, path: str | Path) -> None:
    """Write a GeoDataFrame to GeoPackage, GeoJSON, or GeoParquet."""
    output_path = Path(path).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()

    if suffix == ".gpkg":
        _write_file(gdf, output_path, driver="GPKG")
        return

    if suffix in {".geojson", ".json"}:
        _write_file(gdf, output_path, driver="GeoJSON")
        return

    if suffix == ".parquet":
        try:
            gdf.to_parquet(output_path, index=False)
            return
        except Exception:  # pragma: no cover - depends on optional parquet engines.
            fallback_path = output_path.with_suffix(".gpkg")
            _write_file(gdf, fallback_path, driver="GPKG")
            return

    fallback_path = output_path.with_suffix(".gpkg")
    _write_file(gdf, fallback_path, driver="GPKG")


def _read_csv_points(path: Path, crs: str | None) -> gpd.GeoDataFrame:
    data = pd.read_csv(path)
    lon_col, lat_col = _find_coordinate_columns(data.columns)
    geometry = [Point(xy) for xy in zip(data[lon_col], data[lat_col], strict=True)]
    assigned_crs = crs or "EPSG:4326"
    return gpd.GeoDataFrame(data, geometry=geometry, crs=assigned_crs)


def _find_coordinate_columns(columns: Iterable[str]) -> tuple[str, str]:
    lower_to_original = {column.lower(): column for column in columns}
    for lon_name, lat_name in CSV_COORDINATE_PAIRS:
        if lon_name in lower_to_original and lat_name in lower_to_original:
            return lower_to_original[lon_name], lower_to_original[lat_name]

    expected = ", ".join(f"{x}/{y}" for x, y in CSV_COORDINATE_PAIRS)
    raise ValueError(f"CSV input must include coordinate columns named one of: {expected}")


def _write_file(gdf: gpd.GeoDataFrame, path: Path, driver: str) -> None:
    try:
        gdf.to_file(path, driver=driver, engine="pyogrio")
    except TypeError:
        gdf.to_file(path, driver=driver)
