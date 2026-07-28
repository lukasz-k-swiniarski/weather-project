from datetime import date

from etl_process.station_metadata import (
    _normalize_partial_date,
    decode_source,
    normalize_records,
)


def test_decode_source_handles_windows_1250_and_utf8_values():
    payload = (
        b'[{"nazwa stacji":"WARSZAWA-OK\xcaCIE",'
        b'"uwagi":"BIELSKO-BIA\xc5\x81A"}]'
    )

    [record] = decode_source(payload)

    assert record["nazwa stacji"] == "WARSZAWA-OKĘCIE"
    assert record["uwagi"] == "BIELSKO-BIAŁA"


def test_partial_year_boundary_is_normalized_without_overlap():
    assert _normalize_partial_date(1956, period_end=False) == "1956-01-01"
    assert _normalize_partial_date(1956, period_end=True) == "1955-12-31"


def test_normalize_records_filters_to_project_station_codes():
    records = [
        {
            "kod 9-znakowy": 352200375,
            "nazwa stacji": "Warszawa-Okęcie",
            "data_od": "1951-01-01",
            "data_do": "",
            "rodzaj stacji": "synoptyczna",
            "rząd danych w CBDH": "synop",
            "latitude": "52,166667",
            "longitude": "20,966667",
            "wysokość [m npm]": 106,
        },
        {
            "kod 9-znakowy": 999999999,
            "nazwa stacji": "Outside project",
            "data_od": "1951-01-01",
            "data_do": "",
            "rodzaj stacji": "synoptyczna",
            "rząd danych w CBDH": "synop",
            "latitude": "50,0",
            "longitude": "20,0",
            "wysokość [m npm]": 100,
        },
    ]

    normalized = normalize_records(
        records,
        {352200375},
        retrieved_at=date(2026, 7, 28),
    )

    assert len(normalized) == 1
    assert normalized[0]["official_station_name"] == "WARSZAWA-OKĘCIE"
    assert normalized[0]["latitude"] == "52.166667"
    assert normalized[0]["metadata_status"] == "official"
