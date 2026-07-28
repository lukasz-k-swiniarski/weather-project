from pathlib import Path

SCHEMA_PATH = Path(__file__).parents[1] / "postgresql_db" / "00_schema.sql"


def schema_sql() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8").lower()


def test_schema_defines_dimensional_gold_model():
    sql = schema_sql()

    assert "create table layer_gold.dim_date" in sql
    assert "create table layer_gold.dim_year" in sql
    assert "create table layer_gold.dim_station" in sql
    assert "create table layer_gold.dim_reporting_location" in sql
    assert "create table layer_gold.fact_weather_daily" in sql
    assert "create table layer_gold.fact_weather_station_year" in sql
    assert "primary key (date_key, station_key)" in sql
    assert "foreign key (date_key)" in sql
    assert "foreign key (station_key)" in sql
    assert "foreign key (year) references layer_gold.dim_year (year)" in sql
    assert "foreign key (location_key)" in sql
    assert "unique (station_code, valid_from)" in sql
    assert "weather.observation_date >= station_dimension.valid_from" in sql


def test_reporting_location_is_a_conformed_dimension():
    sql = schema_sql()
    station_definition = sql.split(
        "create table layer_gold.dim_station", maxsplit=1
    )[1].split(");", maxsplit=1)[0]

    assert "location_key bigint not null" in station_definition
    assert "location_name text" not in station_definition
    assert "location_type text" not in station_definition
    assert "voivodeship text" not in station_definition


def test_annual_fact_has_explicit_grain_and_quality_contract():
    sql = schema_sql()

    assert "primary key (station_key, year)" in sql
    assert (
        "foreign key (station_key) references layer_gold.dim_station (station_key)"
        in sql
    )
    assert "expected_days in (365, 366)" in sql
    assert "avg_temperature_coverage >= 0.95" in sql
    assert "max_temperature_coverage >= 0.95" in sql
    assert "min_temperature_coverage >= 0.95" in sql
    assert "precipitation_coverage >= 0.95" in sql
    assert "snow_cover_coverage >= 0.95" in sql
    assert "weather.max_air_temperature_c >= 30" in sql
    assert "weather.max_air_temperature_c >= 35" in sql
    assert "weather.min_air_temperature_c <= -20" in sql
    assert "weather.min_air_temperature_c <= -25" in sql


def test_incomplete_annual_metrics_are_null_in_the_warehouse():
    sql = schema_sql()

    assert "make_date(station_year.year + 1, 1, 1) - 1 <= last_date" in sql
    assert (
        "when quality.is_complete_year and quality.precipitation_coverage >= 0.95"
        in sql
    )
    assert "then quality.raw_precipitation_total_mm" in sql


def test_schema_defines_versioned_station_reference_tables():
    sql = schema_sql()

    assert "create table layer_silver.station_alias" in sql
    assert "create table layer_silver.station_reporting_location" in sql
    assert "create table layer_silver.station_metadata_history" in sql
    assert "primary key (station_code, valid_from)" in sql
    assert "voivodeship text not null" in sql


def test_silver_uses_station_day_grain_and_both_sources():
    sql = schema_sql()

    assert "create table layer_silver.weather_daily" in sql
    assert "primary key (station_code, observation_date)" in sql
    assert "from layer_bronze.synop_s_d_imgw as source" in sql
    assert "left join layer_bronze.synop_s_d_t_imgw as secondary" in sql


def test_schema_does_not_recreate_gold_table_during_refresh():
    sql = schema_sql()

    assert "drop table" not in sql
    assert "create table as" not in sql
    assert "truncate table" in sql


def test_schema_removes_unused_geography_objects_and_pg_dump_commands():
    sql = schema_sql()

    assert "create extension" not in sql
    assert "layer_bronze.geography" not in sql
    assert "layer_silver.geography_city" not in sql
    assert "\\restrict" not in sql
    assert "\\unrestrict" not in sql
