# Configuration

Workflows are controlled by a YAML file.

Input paths are resolved from the current working directory first and then from
the config file directory. Output paths are resolved from the current working
directory so repeated commands write to a predictable `outputs/` folder.

## `project`

Optional metadata used in reports.

- `name`: Project title.
- `description`: Short description.

## `input`

Required input dataset settings.

- `path`: Path to the input dataset.
- `layer`: Optional layer name for multi-layer files such as GeoPackage.
- `crs`: CRS assigned when the input file lacks CRS metadata. CSV inputs default to `EPSG:4326`.

Supported inputs:

- `.geojson`
- `.json`
- `.gpkg`
- `.shp`
- `.csv` with `lon/lat`, `longitude/latitude`, or `x/y` columns

## `output`

Required output settings.

- `dir`: Directory for workflow outputs.
- `cleaned_path`: Path for the cleaned dataset written by `geoaudit fix` or `geoaudit run`.

## `checks`

Enable or disable quality checks:

- `crs`
- `empty_geometry`
- `invalid_geometry`
- `duplicate_geometry`
- `missing_values`
- `geometry_types`
- `bbox`

## `fixes`

Optional cleaning settings.

- `enabled`: Whether fixes should run.
- `repair_geometry`: Repair invalid geometries.
- `drop_empty_geometry`: Drop null or empty geometries.
- `target_crs`: Reproject cleaned data to this CRS.

## `analysis`

Optional list of analysis recipes. See `analysis_recipes.md`.

## `map`

Optional preview map settings.

- `enabled`: Whether to generate an HTML map.
- `output`: Output HTML path.
- `tooltip_columns`: Attribute columns shown in map tooltips.

## `report`

Optional report settings.

- `enabled`: Whether reports should be generated.
- `formats`: Any of `markdown` and `html`.
- `output_dir`: Directory for report files.
