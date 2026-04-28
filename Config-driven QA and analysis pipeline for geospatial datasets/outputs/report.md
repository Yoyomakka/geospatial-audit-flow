# urban-green-space-demo

Audit and analyze urban park polygons by district.

## Dataset

| Field | Value |
| --- | --- |
| Input path | `examples/urban_green_space_demo/data/parks.geojson` |
| CRS | `EPSG:3857` |
| Row count | 8 |
| Geometry types | Polygon: 8 |

## Quality Check Summary

| Status | Count |
| --- | ---: |
| PASS | 7 |
| WARN | 0 |
| FAIL | 0 |
| Total | 7 |

## Quality Checks

| Check | Status | Message |
| --- | --- | --- |
| crs | PASS | Dataset CRS is EPSG:4326. |
| empty_geometry | PASS | No empty geometries found. |
| invalid_geometry | PASS | All non-empty geometries are valid. |
| duplicate_geometry | PASS | No duplicate geometries found. |
| missing_values | PASS | No columns exceed 40% missing values. |
| geometry_types | PASS | Geometry type is consistent. |
| bbox | PASS | Dataset bounds calculated successfully. |


## Analysis Outputs

| Recipe | Rows | Output |
| --- | ---: | --- |
| area_by_category | 8 | `outputs/park_area_by_type.csv` |
| count_by_polygon | 4 | `outputs/parks_by_district.csv` |



## Map

Interactive preview map: `outputs/preview_map.html`


## Suggested Next Steps

- Inspect generated CSV outputs for expected totals.
- Open the preview map and visually spot-check geometry placement.
