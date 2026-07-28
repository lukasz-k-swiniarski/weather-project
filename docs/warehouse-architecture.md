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
- retains status `9` as the explicit absence of a phenomenon;
- retains the secondary daily mean temperature for source reconciliation.

`STD` from `s_d` is the canonical daily mean temperature. `TEMP` from `s_d_t` is not published
as a competing Gold metric because the source values are not always equal.

`SMDB` from `s_d` is the canonical daily precipitation total. `WODZ` and `WONO` remain available
as daytime and nighttime source measures but are not assumed to sum to `SMDB`.

### Gold

Gold is a star schema designed for Power BI:

- `layer_gold.dim_date` contains one row per calendar date;
- `layer_gold.dim_station` contains one row per IMGW station code;
- `layer_gold.fact_weather_daily` contains one row per station and observation date.

The fact table stores foreign keys and measurements only. Station names, locations,
administrative divisions and coordinates belong to `dim_station` and are not repeated across
daily observations.

## Refresh order

`layer_bronze.refresh_etl()` runs:

1. `layer_silver.refresh()`;
2. `layer_gold.refresh()`.

Refresh procedures use stable tables with `TRUNCATE` and `INSERT`. Exceptions propagate to the
Python pipeline so a failed refresh can be reported as a failed ETL run.

Gold refresh refuses to run when:

- Silver contains no weather rows;
- a weather station has no reference mapping;
- one station code maps to more than one location.

## Deferred geographic enrichment

The station dimension contains nullable fields for voivodeship, latitude, longitude and
elevation. They are populated only from a reviewed station metadata source in a separate package.
PostGIS is not required until the project implements an actual spatial operation.
