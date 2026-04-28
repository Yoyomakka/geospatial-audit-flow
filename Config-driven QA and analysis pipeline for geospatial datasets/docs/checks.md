# Quality Checks

## CRS

Passes when the dataset has a coordinate reference system. Warns when CRS metadata is missing.

## Empty Geometry

Checks for null or empty geometries. Warns if some rows are empty and fails if all rows are empty.

## Invalid Geometry

Checks Shapely geometry validity. Warns when invalid geometries are present.

## Duplicate Geometry

Compares geometry WKB values to identify duplicate shapes. Warns when duplicate geometries are found.

## Missing Values

Calculates missing-value ratios for non-geometry columns. Warns when any column has more than 40 percent missing values.

## Geometry Types

Reports geometry type counts such as `Point`, `Polygon`, and `MultiPolygon`. Warns when multiple real geometry types are present.

## Bounding Box

Reports dataset bounds. Warns when EPSG:4326 coordinates fall outside reasonable longitude and latitude ranges.
