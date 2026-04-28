"""Command-line interface for geo-audit-flow."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

import click
import geopandas as gpd

from geoaudit.analysis import run_analysis_recipes
from geoaudit.checks import run_checks, save_check_results
from geoaudit.config import (
    get_output_dir,
    load_config,
    resolve_config_path,
    resolve_output_path,
    validate_config,
)
from geoaudit.fixes import apply_fixes
from geoaudit.io import read_geodata, write_geodata
from geoaudit.map import generate_preview_map
from geoaudit.models import AnalysisResult, CheckResult, WorkflowResult
from geoaudit.report import generate_html_report, generate_markdown_report
from geoaudit.utils import ensure_directory


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="geo-audit-flow")
def main() -> None:
    """Run config-driven QA, cleaning, analysis, maps, and reports for geospatial data."""


@main.command()
def init() -> None:
    """Create a starter geo-audit-flow project in the current directory."""
    root = Path.cwd()
    ensure_directory(root / "data")
    ensure_directory(root / "outputs")

    config_path = root / "config.yml"
    if not config_path.exists():
        config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
        click.echo(f"Created {_display_path(config_path)}")
    else:
        click.echo(f"Skipped existing {_display_path(config_path)}")

    click.echo(
        "Created data/ and outputs/. Add a dataset, update config.yml, "
        "then run geoaudit run config.yml."
    )


@main.command()
@click.argument("config_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def check(config_path: Path) -> None:
    """Run data-quality checks only."""
    try:
        config = _load_and_validate(config_path)
        gdf = _read_configured_input(config)
        results = run_checks(gdf, config)
        output_dir = get_output_dir(config)
        save_check_results(results, output_dir / "check_results.json")
        generate_markdown_report(
            config,
            results,
            [],
            output_dir / "check_report.md",
            dataset_info=_dataset_info(gdf),
        )
    except Exception as exc:
        raise click.ClickException(_safe_text(str(exc))) from exc

    click.echo(f"Ran {len(results)} checks.")
    click.echo(f"Wrote {_display_path(output_dir / 'check_results.json')}")
    click.echo(f"Wrote {_display_path(output_dir / 'check_report.md')}")


@main.command(name="fix")
@click.argument("config_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def fix_command(config_path: Path) -> None:
    """Apply configured fixes and write a cleaned dataset."""
    try:
        config = _load_and_validate(config_path)
        gdf = _read_configured_input(config)
        cleaned = apply_fixes(gdf, config)
        cleaned_path = _cleaned_path(config)
        write_geodata(cleaned, cleaned_path)
    except Exception as exc:
        raise click.ClickException(_safe_text(str(exc))) from exc

    click.echo(f"Wrote cleaned dataset to {_display_path(cleaned_path)}")


@main.command(name="run")
@click.argument("config_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def run_command(config_path: Path) -> None:
    """Run the full QA, fixing, analysis, map, and report workflow."""
    try:
        result, output_dir = _run_workflow(config_path)
    except Exception as exc:
        raise click.ClickException(_safe_text(str(exc))) from exc

    click.echo(f"Ran {len(result.check_results)} checks.")
    if result.cleaned_path:
        click.echo(f"Wrote cleaned dataset to {_display_path(result.cleaned_path)}")
    for analysis_result in result.analysis_results:
        click.echo(
            f"Wrote {analysis_result.recipe_type} output to "
            f"{_display_path(analysis_result.output_path)}"
        )
    if result.map_path:
        click.echo(f"Wrote preview map to {_display_path(result.map_path)}")
    click.echo(f"Wrote reports to {_display_path(output_dir)}")


@main.command()
@click.argument("name", type=click.Choice(["urban-green-space"]))
def example(name: str) -> None:
    """Copy a built-in example project into the current directory."""
    if name != "urban-green-space":
        raise click.ClickException(f"Unknown example: {name}")

    source = _repo_root() / "examples" / "urban_green_space_demo"
    destination = Path.cwd() / "urban_green_space_demo"

    if not source.exists():
        raise click.ClickException(
            "Built-in example files were not found. Run python scripts/make_sample_data.py "
            "from the repository root to regenerate them."
    )
    if destination.exists():
        click.echo(f"Example already exists at {_display_path(destination)}")
    else:
        shutil.copytree(source, destination)
        copied_config = destination / "config.yml"
        copied_config.write_text(
            copied_config.read_text(encoding="utf-8").replace(
                "examples/urban_green_space_demo/data",
                f"{destination.name}/data",
            ),
            encoding="utf-8",
        )
        click.echo(f"Copied example to {_display_path(destination)}")

    click.echo("Run: geoaudit run urban_green_space_demo/config.yml")


def _run_workflow(config_path: Path) -> tuple[WorkflowResult, Path]:
    config = _load_and_validate(config_path)
    gdf = _read_configured_input(config)
    output_dir = get_output_dir(config)

    check_results = run_checks(gdf, config)
    save_check_results(check_results, output_dir / "check_results.json")
    generate_markdown_report(
        config,
        check_results,
        [],
        output_dir / "check_report.md",
        dataset_info=_dataset_info(gdf),
    )

    working_gdf = gdf
    cleaned_path: Path | None = None
    fixes = config.get("fixes", {})
    if isinstance(fixes, dict) and bool(fixes.get("enabled", False)):
        working_gdf = apply_fixes(gdf, config)
        cleaned_path = _cleaned_path(config)
        write_geodata(working_gdf, cleaned_path)

    analysis_results = run_analysis_recipes(working_gdf, config)
    map_path = _maybe_generate_map(working_gdf, config)
    report_paths = _maybe_generate_reports(
        config,
        check_results,
        analysis_results,
        output_dir,
        _dataset_info(working_gdf),
        map_path,
    )

    return (
        WorkflowResult(
            check_results=check_results,
            analysis_results=analysis_results,
            cleaned_path=cleaned_path,
            map_path=map_path,
            report_paths=report_paths,
        ),
        output_dir,
    )


def _load_and_validate(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    validate_config(config)
    return config


def _read_configured_input(config: dict[str, Any]) -> gpd.GeoDataFrame:
    input_config = config["input"]
    input_path = resolve_config_path(config, str(input_config["path"]))
    layer = input_config.get("layer")
    crs = input_config.get("crs")
    click.echo(f"Reading {_display_path(input_path)}")
    return read_geodata(
        input_path,
        layer=str(layer) if layer is not None else None,
        crs=str(crs) if crs is not None else None,
    )


def _cleaned_path(config: dict[str, Any]) -> Path:
    output_config = config.get("output", {})
    if isinstance(output_config, dict) and output_config.get("cleaned_path"):
        return resolve_output_path(config, str(output_config["cleaned_path"]))
    return get_output_dir(config) / "cleaned.gpkg"


def _maybe_generate_map(gdf: gpd.GeoDataFrame, config: dict[str, Any]) -> Path | None:
    map_config = config.get("map", {})
    if not isinstance(map_config, dict) or not bool(map_config.get("enabled", False)):
        return None

    output_raw = map_config.get("output", get_output_dir(config) / "preview_map.html")
    output_path = resolve_output_path(config, str(output_raw))
    tooltip_columns = map_config.get("tooltip_columns", [])
    if not isinstance(tooltip_columns, list):
        tooltip_columns = []
    generate_preview_map(gdf, output_path, [str(column) for column in tooltip_columns])
    return output_path


def _maybe_generate_reports(
    config: dict[str, Any],
    check_results: list[CheckResult],
    analysis_results: list[AnalysisResult],
    output_dir: Path,
    dataset_info: dict[str, Any],
    map_path: Path | None,
) -> list[Path]:
    report_config = config.get("report", {"enabled": True, "formats": ["markdown", "html"]})
    if not isinstance(report_config, dict) or not bool(report_config.get("enabled", False)):
        return []

    formats = report_config.get("formats", ["markdown"])
    if not isinstance(formats, list):
        formats = ["markdown"]

    report_output_dir = resolve_output_path(
        config,
        str(report_config.get("output_dir", output_dir)),
    )
    report_output_dir.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    markdown_path = report_output_dir / "report.md"
    if "markdown" in formats or "html" in formats:
        generate_markdown_report(
            config,
            check_results,
            analysis_results,
            markdown_path,
            dataset_info=dataset_info,
            map_output=map_path,
        )
        paths.append(markdown_path)

    if "html" in formats:
        html_path = report_output_dir / "report.html"
        generate_html_report(markdown_path, html_path)
        paths.append(html_path)

    return paths


def _dataset_info(gdf: gpd.GeoDataFrame) -> dict[str, Any]:
    return {
        "row_count": len(gdf),
        "crs": str(gdf.crs) if gdf.crs is not None else "undefined",
    }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _display_path(path: str | Path) -> str:
    path_obj = Path(path)
    try:
        display = path_obj.relative_to(Path.cwd()).as_posix()
    except ValueError:
        display = str(path_obj)
    return _safe_text(display)


def _safe_text(value: str) -> str:
    encoding = sys.stdout.encoding or "utf-8"
    return value.encode(encoding, errors="backslashreplace").decode(encoding)


DEFAULT_CONFIG = """project:
  name: my-geo-audit-project
  description: Repeatable QA and lightweight analysis for a geospatial dataset.

input:
  path: data/input.geojson
  layer: null
  crs: EPSG:4326

output:
  dir: outputs
  cleaned_path: outputs/cleaned.gpkg

checks:
  crs: true
  empty_geometry: true
  invalid_geometry: true
  duplicate_geometry: true
  missing_values: true
  geometry_types: true
  bbox: true

fixes:
  enabled: true
  repair_geometry: true
  drop_empty_geometry: true
  target_crs: EPSG:3857

analysis: []

map:
  enabled: true
  output: outputs/preview_map.html
  tooltip_columns: []

report:
  enabled: true
  formats:
    - markdown
    - html
  output_dir: outputs
"""
