"""Data-quality checks for GeoDataFrames."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import geopandas as gpd

from geoaudit.models import CheckResult, CheckSummary


def check_crs(gdf: gpd.GeoDataFrame) -> CheckResult:
    """Check whether the dataset has a coordinate reference system."""
    if gdf.crs is None:
        return CheckResult("crs", "WARN", "Dataset has no CRS defined.", None)
    return CheckResult("crs", "PASS", f"Dataset CRS is {gdf.crs}.", str(gdf.crs))


def check_empty_geometry(gdf: gpd.GeoDataFrame) -> CheckResult:
    """Check for null or empty geometries."""
    total = len(gdf)
    if total == 0:
        return CheckResult("empty_geometry", "FAIL", "Dataset contains no rows.", {"count": 0})

    empty_mask = gdf.geometry.isna() | gdf.geometry.is_empty
    empty_count = int(empty_mask.sum())
    value = {"empty_count": empty_count, "row_count": total}

    if empty_count == 0:
        return CheckResult("empty_geometry", "PASS", "No empty geometries found.", value)
    if empty_count == total:
        return CheckResult("empty_geometry", "FAIL", "All geometries are empty or null.", value)
    return CheckResult("empty_geometry", "WARN", f"{empty_count} empty geometries found.", value)


def check_invalid_geometry(gdf: gpd.GeoDataFrame) -> CheckResult:
    """Check for invalid geometries."""
    non_empty_mask = gdf.geometry.notna() & ~gdf.geometry.is_empty
    invalid_mask = non_empty_mask & ~gdf.geometry.is_valid
    invalid_count = int(invalid_mask.sum())
    value = {"invalid_count": invalid_count, "row_count": len(gdf)}

    if invalid_count == 0:
        return CheckResult("invalid_geometry", "PASS", "All non-empty geometries are valid.", value)
    return CheckResult(
        "invalid_geometry",
        "WARN",
        f"{invalid_count} invalid geometries found.",
        value,
    )


def check_duplicate_geometry(gdf: gpd.GeoDataFrame) -> CheckResult:
    """Check for duplicated geometry values using WKB."""
    wkb_values = gdf.geometry.apply(
        lambda geometry: geometry.wkb_hex
        if geometry is not None and not getattr(geometry, "is_empty", True)
        else None
    )
    duplicate_count = int(wkb_values.dropna().duplicated(keep=False).sum())
    value = {"duplicate_geometry_count": duplicate_count}

    if duplicate_count == 0:
        return CheckResult("duplicate_geometry", "PASS", "No duplicate geometries found.", value)
    return CheckResult(
        "duplicate_geometry",
        "WARN",
        f"{duplicate_count} rows have duplicate geometries.",
        value,
    )


def check_missing_values(gdf: gpd.GeoDataFrame) -> CheckResult:
    """Summarize missing values in non-geometry columns."""
    non_geometry_columns = [column for column in gdf.columns if column != gdf.geometry.name]
    ratios = {
        str(column): float(gdf[column].isna().mean()) if len(gdf) else 0.0
        for column in non_geometry_columns
    }
    high_missing = {
        column: ratio for column, ratio in ratios.items() if ratio > 0.4
    }

    if not high_missing:
        return CheckResult(
            "missing_values",
            "PASS",
            "No columns exceed 40% missing values.",
            ratios,
        )

    columns = ", ".join(sorted(high_missing))
    return CheckResult(
        "missing_values",
        "WARN",
        f"Columns exceed 40% missing values: {columns}.",
        ratios,
    )


def check_geometry_types(gdf: gpd.GeoDataFrame) -> CheckResult:
    """Report geometry type counts and warn when multiple types are present."""
    type_counts = {
        str(geometry_type): int(count)
        for geometry_type, count in gdf.geometry.geom_type.fillna("None").value_counts().items()
    }
    real_types = {geometry_type for geometry_type in type_counts if geometry_type != "None"}

    if len(real_types) <= 1:
        return CheckResult("geometry_types", "PASS", "Geometry type is consistent.", type_counts)

    return CheckResult(
        "geometry_types",
        "WARN",
        "Mixed geometry types found.",
        type_counts,
    )


def check_bbox(gdf: gpd.GeoDataFrame) -> CheckResult:
    """Report total bounds and warn for impossible EPSG:4326 bounds."""
    if len(gdf) == 0 or bool(gdf.geometry.isna().all()):
        return CheckResult("bbox", "WARN", "Cannot calculate bounds for an empty dataset.", None)

    minx, miny, maxx, maxy = [float(value) for value in gdf.total_bounds]
    value = {"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy}

    if gdf.crs is not None and gdf.crs.to_epsg() == 4326:
        outside_lon = minx < -180 or maxx > 180
        outside_lat = miny < -90 or maxy > 90
        if outside_lon or outside_lat:
            return CheckResult(
                "bbox",
                "WARN",
                "EPSG:4326 bounds fall outside reasonable longitude/latitude ranges.",
                value,
            )

    return CheckResult("bbox", "PASS", "Dataset bounds calculated successfully.", value)


def run_checks(gdf: gpd.GeoDataFrame, config: dict[str, Any]) -> list[CheckResult]:
    """Run enabled quality checks from config."""
    checks_config = config.get("checks", {})
    if not isinstance(checks_config, dict):
        raise ValueError("Config section 'checks' must be a mapping.")

    available_checks = {
        "crs": check_crs,
        "empty_geometry": check_empty_geometry,
        "invalid_geometry": check_invalid_geometry,
        "duplicate_geometry": check_duplicate_geometry,
        "missing_values": check_missing_values,
        "geometry_types": check_geometry_types,
        "bbox": check_bbox,
    }

    results: list[CheckResult] = []
    for check_name, check_function in available_checks.items():
        if bool(checks_config.get(check_name, False)):
            results.append(check_function(gdf))
    return results


def summarize_checks(results: list[CheckResult]) -> dict[str, int]:
    """Summarize check statuses as plain counts."""
    summary = CheckSummary(
        total=len(results),
        passed=sum(result.status == "PASS" for result in results),
        warnings=sum(result.status == "WARN" for result in results),
        failed=sum(result.status == "FAIL" for result in results),
    )
    return summary.to_dict()


def save_check_results(results: list[CheckResult], output_path: str | Path) -> None:
    """Write check results and a summary to JSON."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": summarize_checks(results),
        "results": [result.to_dict() for result in results],
    }
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
