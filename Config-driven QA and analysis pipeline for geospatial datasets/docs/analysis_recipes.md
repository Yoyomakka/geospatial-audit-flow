# Analysis Recipes

## `area_by_category`

Calculates feature area in square meters and groups results by an attribute column.

Required fields:

- `type: area_by_category`
- `category_column`
- `output`

Output columns:

- `category`
- `feature_count`
- `total_area_sqm`
- `mean_area_sqm`

For geographic CRS inputs, the recipe reprojects to `fixes.target_crs` when configured, otherwise `EPSG:3857`.

## `count_by_polygon`

Counts input features intersecting each polygon in a boundary dataset.

Required fields:

- `type: count_by_polygon`
- `polygon_path`
- `polygon_name_column`
- `output`

Output columns:

- `polygon_name`
- `feature_count`

## `nearest_feature`

Finds the nearest target feature for each source feature.

Required fields:

- `type: nearest_feature`
- `target_path`
- `output`

Output columns:

- `source_index`
- `nearest_target_index`
- `distance_m`
