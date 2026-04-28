# geo-audit-flow

[![CI](https://github.com/your-org/geo-audit-flow/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/geo-audit-flow/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A config-driven QA, cleaning, lightweight spatial analysis, and report-generation pipeline for geospatial datasets.

## Why this project exists

Geospatial datasets often arrive with unclear CRS metadata, invalid geometries, missing attributes, duplicate features, and no repeatable audit trail. `geo-audit-flow` provides a small, laptop-friendly workflow for checking, cleaning, analyzing, mapping, and reporting on vector geospatial data from a single YAML config file.

It is designed for students, analysts, and portfolio projects that need practical GIS automation without a database server, cloud stack, or web application.

## Features

- YAML-driven workflows for repeatable geospatial QA.
- Input support for GeoJSON, GeoPackage, Shapefile, and CSV point data.
- Quality checks for CRS, empty geometries, invalid geometries, duplicates, missing values, geometry types, and bounds.
- Optional fixes for empty geometries, invalid geometries, and reprojection.
- Analysis recipes for area by category, counts by polygon, and nearest-feature distance.
- CSV outputs, interactive Folium preview maps, and Markdown/HTML reports.
- Click-based CLI named `geoaudit`.
- Tests, linting, typing config, GitHub Actions CI, docs, and contribution files.

## Installation

```bash
git clone https://github.com/your-org/geo-audit-flow.git
cd geo-audit-flow
pip install -e ".[dev]"
```

## Quickstart

Generate or refresh the included synthetic sample data:

```bash
python scripts/make_sample_data.py
```

Run the complete demo workflow:

```bash
geoaudit run examples/urban_green_space_demo/config.yml
```

Open:

- `outputs/report.html`
- `outputs/preview_map.html`

## Example YAML Configuration

```yaml
project:
  name: urban-green-space-demo
  description: Audit and analyze urban park polygons by district.

input:
  path: examples/urban_green_space_demo/data/parks.geojson
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

analysis:
  - type: area_by_category
    category_column: park_type
    output: outputs/park_area_by_type.csv

  - type: count_by_polygon
    polygon_path: examples/urban_green_space_demo/data/districts.geojson
    polygon_name_column: district_name
    output: outputs/parks_by_district.csv

map:
  enabled: true
  output: outputs/preview_map.html
  tooltip_columns:
    - name
    - park_type

report:
  enabled: true
  formats:
    - markdown
    - html
  output_dir: outputs
```

## CLI Usage

```bash
geoaudit --help
geoaudit init
geoaudit check config.yml
geoaudit fix config.yml
geoaudit run config.yml
geoaudit example urban-green-space
```

## Example Output Structure

```text
outputs/
├── check_results.json
├── check_report.md
├── cleaned.gpkg
├── park_area_by_type.csv
├── parks_by_district.csv
├── preview_map.html
├── report.md
└── report.html
```

## Development Setup

```bash
pip install -e ".[dev]"
ruff check .
mypy src
pytest
```

## Running Tests

```bash
pytest
```

## Roadmap

- DuckDB Spatial backend.
- OSMnx network accessibility recipe.
- PySAL spatial statistics recipes.
- GeoParquet support improvements.
- Vector tile export.
- Richer data-quality scoring.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, coding standards, and pull request expectations.

## License

MIT License. See [LICENSE](LICENSE).
