# Warehouse architecture

## Layer responsibilities

### Bronze

Bronze preserves the two source-shaped IMGW daily SYNOP datasets:

- `layer_bronze.synop_s_d_imgw`
- `layer_bronze.synop_s_d_t_imgw`

Column names and measurement statuses remain faithful to IMGW. Bronze tables are stable schema
objects: a load truncates and repopulates them inside a database transaction instead of dropping
and recreating them through pandas.

### Silver

`layer_silver.weather_daily` has one row per:

```text
station_code + observation_date
```

The primary `s_d` source drives row coverage. The secondary `s_d_t` source is joined with a
left join because it has a shorter historical and current coverage range.

Silver:

- converts source date components to a PostgreSQL `date`;
- gives measurements explicit names and units;
- retains IMGW measurement statuses;
- converts values with status `8` (missing measurement) to `NULL`;
- normalizes a missing numeric precipitation value with status `9` to `0 mm`,
  while retaining status `9` as the explicit absence of the phenomenon;
- retains the secondary daily mean temperature for source reconciliation.

Station reference data is separated by responsibility:

- `station_alias` resolves historical names from the measurement files;
- `station_metadata_history` preserves official IMGW metadata validity periods;
- `station_reporting_location` provides stable reporting locations and contemporary
  voivodeships for BI.

`STD` from `s_d` is the canonical daily mean temperature. `TEMP` from `s_d_t` is not published
as a competing Gold metric because the source values are not always equal.

`SMDB` from `s_d` is the canonical daily precipitation total. `WODZ` and `WONO` remain available
as daytime and nighttime source measures but are not assumed to sum to `SMDB`.

### Gold

Gold is a star schema designed for Power BI:

- `layer_gold.dim_date` contains one row per calendar date;
- `layer_gold.dim_year` contains one row per calendar year and identifies incomplete years;
- `layer_gold.dim_station` contains one stable row per IMGW station code;
- `layer_gold.dim_station_version` is an SCD Type 2 dimension with one row per station
  metadata validity period;
- `layer_gold.dim_reporting_location` contains one row per stable BI reporting location;
- `layer_gold.fact_weather_daily` contains one row per station and observation date.
- `layer_gold.fact_weather_station_year` contains one row per stable station and calendar year.

The fact tables store foreign keys and measurements only. Each daily observation references both
the stable station and exactly one historical version selected by station code and observation
date. Official historical names, coordinates and elevation belong to `dim_station_version`.
Stable reporting locations and voivodeships belong to the conformed
`dim_reporting_location`, which filters both daily and annual facts through `dim_station`.

`dim_year` filters `dim_date` and the annual fact. This avoids a many-to-many relationship between
daily dates and station-year rows in the Power BI semantic model.

`metadata_status` distinguishes official IMGW versions from explicit `unavailable` coverage
periods. Unavailable periods retain reporting geography but never infer coordinates or elevation.

The annual fact is a quality-gated aggregate for Power BI. It calculates completeness separately
for each source measure and publishes an annual value only for a completed year with at least 95%
coverage. See [BI metric contract](metric-contract.md) for metric formulas and aggregation rules.

## Refresh order

`layer_bronze.refresh_etl()` runs:

1. `layer_silver.refresh()`;
2. `layer_gold.refresh()`.

Refresh procedures use stable tables with `TRUNCATE` and `INSERT`. Exceptions propagate to the
Python pipeline so a failed refresh can be reported as a failed ETL run.

Gold refresh refuses to run when:

- Silver contains no weather rows;
- a weather station has no reference mapping;
- one station code maps to more than one reporting location;
- an observation matches zero or multiple station metadata periods.

## Geographic scope

Latitude, longitude and elevation follow the official historical IMGW metadata period valid for
the observation. Voivodeship is a contemporary reporting classification and does not attempt to
reconstruct historical administrative boundaries. PostGIS remains deferred until the project
implements an actual spatial operation.
