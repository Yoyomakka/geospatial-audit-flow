# Urban Green Space Demo

This example uses small, fictional geospatial datasets for an imaginary city:

- `parks.geojson` contains park polygons with a park name, type, and district hint.
- `districts.geojson` contains four simple district polygons.

The data is synthetic and license-safe. It is intentionally small so the full workflow runs quickly on a laptop.

## Run the Example

From the repository root:

```bash
pip install -e ".[dev]"
geoaudit run examples/urban_green_space_demo/config.yml
```

If you want to regenerate the sample data first:

```bash
python scripts/make_sample_data.py
```

## Expected Outputs

The workflow writes:

- `outputs/check_results.json`
- `outputs/check_report.md`
- `outputs/cleaned.gpkg`
- `outputs/park_area_by_type.csv`
- `outputs/parks_by_district.csv`
- `outputs/preview_map.html`
- `outputs/report.md`
- `outputs/report.html`

Open `outputs/report.html` and `outputs/preview_map.html` to review the results visually.
