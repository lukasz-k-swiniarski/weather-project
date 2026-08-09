import os
from datetime import date
from pathlib import Path

import psycopg2
import pytest

SCHEMA_PATH = Path(__file__).parents[1] / "postgresql_db" / "00_schema.sql"
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is required for PostgreSQL integration tests",
)


@pytest.fixture
def database():
    connection = psycopg2.connect(TEST_DATABASE_URL)
    connection.autocommit = True

    with connection.cursor() as cursor:
        cursor.execute(
            "DROP SCHEMA IF EXISTS layer_gold, layer_silver, layer_bronze CASCADE"
        )
        cursor.execute(SCHEMA_PATH.read_text(encoding="utf-8"))

    try:
        yield connection
    finally:
        connection.close()


def test_station_year_metrics_enforce_measure_specific_coverage(database):
    with database.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO layer_silver.station_reporting_location (
                location_id, location_name, location_type, voivodeship,
                source_url, source_as_of
            )
            VALUES ('LOC001', 'Test City', 'city', 'Test Voivodeship',
                    'https://example.test', DATE '2026-01-01');

            INSERT INTO layer_silver.station_alias (
                station_name, station_code, location_id
            )
            VALUES
                ('STATION A', 100, 'LOC001'),
                ('STATION B', 200, 'LOC001');

            INSERT INTO layer_silver.station_metadata_history (
                station_code, official_station_name, valid_from, valid_to,
                metadata_status, source_url, source_retrieved_at
            )
            VALUES
                (100, 'Station A', DATE '2010-01-01', NULL, 'official',
                 'https://example.test', DATE '2026-01-01'),
                (200, 'Station B', DATE '2010-01-01', NULL, 'official',
                 'https://example.test', DATE '2026-01-01');

            INSERT INTO layer_silver.weather_daily (
                station_code, station_name, observation_date,
                avg_air_temperature_c, max_air_temperature_c,
                min_air_temperature_c, precipitation_total_mm,
                snow_cover_occurred
            )
            SELECT
                station.station_code,
                station.station_name,
                day::date,
                station.avg_temperature,
                CASE
                    WHEN station.station_code = 100 AND day = DATE '2020-01-01' THEN 30
                    WHEN station.station_code = 100 AND day = DATE '2020-01-02' THEN 35
                    ELSE 20
                END,
                CASE
                    WHEN station.station_code = 100 AND day = DATE '2020-01-01' THEN -20
                    WHEN station.station_code = 100 AND day = DATE '2020-01-02' THEN -25
                    ELSE 0
                END,
                CASE
                    WHEN station.station_code = 100 AND day > DATE '2020-12-11' THEN NULL
                    ELSE 2
                END,
                day <= DATE '2020-01-03'
            FROM (
                VALUES
                    (100::bigint, 'STATION A'::text, 10::double precision),
                    (200::bigint, 'STATION B'::text, 30::double precision)
            ) AS station(station_code, station_name, avg_temperature)
            CROSS JOIN generate_series(
                DATE '2020-01-01', DATE '2020-12-31', INTERVAL '1 day'
            ) AS days(day);

            INSERT INTO layer_silver.weather_daily (
                station_code, station_name, observation_date,
                avg_air_temperature_c, max_air_temperature_c,
                min_air_temperature_c, precipitation_total_mm,
                snow_cover_occurred
            )
            SELECT
                100, 'STATION A', day::date, 99, 99, -99, 99, true
            FROM generate_series(
                DATE '2021-01-01', DATE '2021-04-10', INTERVAL '1 day'
            ) AS days(day);

            CALL layer_gold.refresh();
            """
        )

        cursor.execute(
            """
            SELECT
                expected_days,
                is_complete_year,
                precipitation_observed_days,
                is_precipitation_reportable,
                annual_precipitation_total_mm,
                hot_days_ge_30_c,
                very_hot_days_ge_35_c,
                cold_nights_le_minus_20_c,
                very_cold_nights_le_minus_25_c
            FROM layer_gold.fact_weather_station_year AS fact
            JOIN layer_gold.dim_station AS station
                ON station.station_key = fact.station_key
            WHERE station.station_code = 100 AND fact.year = 2020
            """
        )
        complete_year = cursor.fetchone()

        assert complete_year == (366, True, 346, False, None, 2, 1, 2, 1)

        cursor.execute(
            """
            SELECT
                is_complete_year,
                annual_avg_air_temperature_c,
                annual_precipitation_total_mm
            FROM layer_gold.fact_weather_station_year AS fact
            JOIN layer_gold.dim_station AS station
                ON station.station_key = fact.station_key
            WHERE station.station_code = 100 AND fact.year = 2021
            """
        )
        assert cursor.fetchone() == (False, None, None)

        cursor.execute(
            """
            SELECT
                avg(annual_avg_air_temperature_c),
                avg(annual_precipitation_total_mm),
                count(annual_precipitation_total_mm)
            FROM layer_gold.fact_weather_station_year
            WHERE year = 2020
            """
        )
        regional_metrics = cursor.fetchone()

        assert regional_metrics[0] == pytest.approx(20)
        assert regional_metrics[1] == pytest.approx(732)
        assert regional_metrics[2] == 1


def test_silver_distinguishes_absent_precipitation_from_missing_measurement(database):
    with database.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO layer_bronze.synop_s_d_imgw (
                nsp, post, rok, mc, dz, smdb, wsmdb
            )
            VALUES
                (100, 'STATION A', 2024, 1, 1, NULL, 9),
                (100, 'STATION A', 2024, 1, 2, 0, 8),
                (100, 'STATION A', 2024, 1, 3, 2.5, NULL);

            CALL layer_silver.refresh();

            SELECT
                observation_date,
                precipitation_total_mm,
                precipitation_total_status
            FROM layer_silver.weather_daily
            ORDER BY observation_date;
            """
        )

        assert cursor.fetchall() == [
            (date(2024, 1, 1), 0.0, 9),
            (date(2024, 1, 2), None, 8),
            (date(2024, 1, 3), 2.5, None),
        ]
