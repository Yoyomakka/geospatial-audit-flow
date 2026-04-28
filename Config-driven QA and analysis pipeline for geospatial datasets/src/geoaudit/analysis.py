"""Lightweight spatial analysis recipes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

from geoaudit.config import resolve_config_path, resolve_output_path
from geoaudit.io import read_geodata
from geoaudit.models import AnalysisResult

DEFAULT_PROJECTED_CRS = "EPSG:3857"


def run_analysis_recipes(gdf: gpd.GeoDataFrame, config: dict[str, Any]) -> list[AnalysisResult]:
    """Run configured analysis recipes."""
    recipes = config.get("analysis", [])
    if recipes is None:
        return []
    if not isinstance(recipes, list):
        raise ValueError("Config section 'analysis' must be a list.")

    results: list[AnalysisResult] = []
    for recipe in recipes:
        if not isinstance(recipe, dict):
            raise ValueError("Each analysis recipe must be a mapping.")

        recipe_type = recipe.get("type")
        if recipe_type == "area_by_category":
            results.append(area_by_category(gdf, config, recipe))
        elif recipe_type == "count_by_polygon":
            results.append(count_by_polygon(gdf, config, recipe))
        elif recipe_type == "nearest_feature":
            results.append(nearest_feature(gdf, config, recipe))
        else:
            raise ValueError(f"Unknown analysis recipe type: {recipe_type}")

    return results


def area_by_category(
    gdf: gpd.GeoDataFrame,
    config: dict[str, Any],
    recipe: dict[str, Any],
) -> AnalysisResult:
    """Calculate area summaries grouped by a category column."""
    category_column = str(recipe.get("category_column", ""))
    if not category_column or category_column not in gdf.columns:
        raise ValueError(
            f"area_by_category requires an existing category column: {category_column}"
        )

    output_path = _recipe_output_path(config, recipe)
    area_gdf = _project_for_distance_or_area(gdf, config)
    area_gdf = area_gdf.copy()
    area_gdf["__geoaudit_area_sqm"] = area_gdf.geometry.area

    grouped = (
        area_gdf.groupby(category_column, dropna=False)
        .agg(
            feature_count=("__geoaudit_area_sqm", "size"),
            total_area_sqm=("__geoaudit_area_sqm", "sum"),
            mean_area_sqm=("__geoaudit_area_sqm", "mean"),
        )
        .reset_index()
        .rename(columns={category_column: "category"})
    )

    grouped.to_csv(output_path, index=False)
    return AnalysisResult(
        recipe_type="area_by_category",
        output_path=output_path,
        row_count=len(grouped),
        message=f"Wrote area summary by {category_column}.",
    )


def count_by_polygon(
    gdf: gpd.GeoDataFrame,
    config: dict[str, Any],
    recipe: dict[str, Any],
) -> AnalysisResult:
    """Count main dataset features intersecting each polygon."""
    polygon_path_raw = recipe.get("polygon_path")
    if not polygon_path_raw:
        raise ValueError("count_by_polygon requires 'polygon_path'.")

    polygon_path = resolve_config_path(config, str(polygon_path_raw))
    polygon_name_column = str(recipe.get("polygon_name_column", "polygon_name"))
    output_path = _recipe_output_path(config, recipe)

    polygons = read_geodata(polygon_path).reset_index(drop=True)
    if polygon_name_column not in polygons.columns:
        polygons = polygons.copy()
        polygons[polygon_name_column] = polygons.index.astype(str)

    aligned_gdf = _align_to_polygons_crs(gdf, polygons)
    polygon_id = "__geoaudit_polygon_id"
    polygons = polygons.copy()
    polygons[polygon_id] = polygons.index

    joined = gpd.sjoin(
        aligned_gdf,
        polygons[[polygon_id, polygon_name_column, "geometry"]],
        how="left",
        predicate="intersects",
    )
    counts = joined.dropna(subset=[polygon_id]).groupby(polygon_id).size()
    rows = [
        {
            "polygon_name": polygons.loc[index, polygon_name_column],
            "feature_count": int(counts.get(index, 0)),
        }
        for index in polygons.index
    ]

    output = pd.DataFrame(rows)
    output.to_csv(output_path, index=False)
    return AnalysisResult(
        recipe_type="count_by_polygon",
        output_path=output_path,
        row_count=len(output),
        message=f"Wrote feature counts for {len(output)} polygons.",
    )


def nearest_feature(
    gdf: gpd.GeoDataFrame,
    config: dict[str, Any],
    recipe: dict[str, Any],
) -> AnalysisResult:
    """Find the nearest target feature for each source feature."""
    target_path_raw = recipe.get("target_path")
    if not target_path_raw:
        raise ValueError("nearest_feature requires 'target_path'.")

    output_path = _recipe_output_path(config, recipe)
    target_path = resolve_config_path(config, str(target_path_raw))
    targets = read_geodata(target_path)

    source_projected = _project_for_distance_or_area(gdf, config).reset_index(drop=False)
    source_projected = source_projected.rename(columns={"index": "source_index"})
    target_projected = _project_for_distance_or_area(targets, config).reset_index(drop=False)
    target_projected = target_projected.rename(columns={"index": "nearest_target_index"})

    joined = gpd.sjoin_nearest(
        source_projected,
        target_projected[["nearest_target_index", "geometry"]],
        how="left",
        distance_col="distance_m",
    )
    output = joined[["source_index", "nearest_target_index", "distance_m"]].copy()
    output.to_csv(output_path, index=False)

    return AnalysisResult(
        recipe_type="nearest_feature",
        output_path=output_path,
        row_count=len(output),
        message=f"Wrote nearest-feature distances for {len(output)} source features.",
    )


def _recipe_output_path(config: dict[str, Any], recipe: dict[str, Any]) -> Path:
    raw_output = recipe.get("output")
    if not raw_output:
        raise ValueError("Analysis recipe requires 'output'.")
    output_path = resolve_output_path(config, str(raw_output))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def _project_for_distance_or_area(
    gdf: gpd.GeoDataFrame,
    config: dict[str, Any],
) -> gpd.GeoDataFrame:
    target_crs = _analysis_target_crs(config)
    if gdf.crs is None:
        return gdf.set_crs("EPSG:4326").to_crs(target_crs)
    if gdf.crs.is_geographic:
        return gdf.to_crs(target_crs)
    return gdf


def _analysis_target_crs(config: dict[str, Any]) -> str:
    fixes = config.get("fixes", {})
    if isinstance(fixes, dict) and fixes.get("target_crs"):
        return str(fixes["target_crs"])
    return DEFAULT_PROJECTED_CRS


def _align_to_polygons_crs(
    gdf: gpd.GeoDataFrame,
    polygons: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    if polygons.crs is None or gdf.crs is None or gdf.crs == polygons.crs:
        return gdf
    return gdf.to_crs(polygons.crs)
