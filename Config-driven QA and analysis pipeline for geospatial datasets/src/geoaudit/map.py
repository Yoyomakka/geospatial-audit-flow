"""Interactive map generation."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import folium
import geopandas as gpd


def generate_preview_map(
    gdf: gpd.GeoDataFrame,
    output_path: str | Path,
    tooltip_columns: Sequence[str] | None = None,
) -> None:
    """Generate a lightweight interactive HTML preview map."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    map_gdf = _prepare_map_data(gdf)
    center = _map_center(map_gdf)
    folium_map = folium.Map(location=center, zoom_start=12, tiles="OpenStreetMap")

    if len(map_gdf) > 0:
        existing_tooltips = [
            column for column in (tooltip_columns or []) if column in map_gdf.columns
        ]
        tooltip = folium.GeoJsonTooltip(fields=existing_tooltips) if existing_tooltips else None
        folium.GeoJson(
            map_gdf.to_json(),
            name="Input features",
            tooltip=tooltip,
        ).add_to(folium_map)
        folium.LayerControl().add_to(folium_map)

    folium_map.save(destination)


def _prepare_map_data(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    map_gdf = gdf.copy()
    if len(map_gdf) > 1000:
        map_gdf = map_gdf.sample(1000, random_state=42)
    if map_gdf.crs is None:
        map_gdf = map_gdf.set_crs("EPSG:4326")
    elif map_gdf.crs.to_epsg() != 4326:
        map_gdf = map_gdf.to_crs("EPSG:4326")
    return map_gdf


def _map_center(gdf: gpd.GeoDataFrame) -> list[float]:
    if len(gdf) == 0 or bool(gdf.geometry.isna().all()):
        return [0.0, 0.0]

    minx, miny, maxx, maxy = [float(value) for value in gdf.total_bounds]
    return [(miny + maxy) / 2, (minx + maxx) / 2]
