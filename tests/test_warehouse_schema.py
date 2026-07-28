from pathlib import Path

SCHEMA_PATH = Path(__file__).parents[1] / "postgresql_db" / "00_schema.sql"


def schema_sql() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8").lower()


def test_schema_defines_dimensional_gold_model():
    sql = schema_sql()

    assert "create table layer_gold.dim_date" in sql
    assert "create table layer_gold.dim_station" in sql
    assert "create table layer_gold.fact_weather_daily" in sql
    assert "primary key (date_key, station_key)" in sql
    assert "foreign key (date_key)" in sql
    assert "foreign key (station_key)" in sql


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
