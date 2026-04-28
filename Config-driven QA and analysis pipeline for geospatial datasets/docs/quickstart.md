# Quickstart

## Install

```bash
pip install -e ".[dev]"
```

## Create sample data

```bash
python scripts/make_sample_data.py
```

## Run the built-in example

```bash
geoaudit run examples/urban_green_space_demo/config.yml
```

## Inspect outputs

The default example writes outputs to `outputs/`:

- `check_results.json`
- `check_report.md`
- `cleaned.gpkg`
- `park_area_by_type.csv`
- `parks_by_district.csv`
- `preview_map.html`
- `report.md`
- `report.html`

Open `report.html` for a readable workflow summary and `preview_map.html` for a quick spatial sanity check.

## Start your own project

```bash
mkdir my-audit
cd my-audit
geoaudit init
```

Put data in `data/`, edit `config.yml`, then run:

```bash
geoaudit run config.yml
```
