"""Build the versioned IMGW station metadata snapshot used by the warehouse."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import requests

SOURCE_URL = "https://klimat.imgw.pl/json/stacje.json"
OUTPUT_COLUMNS = (
    "station_code",
    "official_station_name",
    "valid_from",
    "valid_to",
    "station_type",
    "data_rank",
    "latitude",
    "longitude",
    "elevation_m",
    "metadata_status",
    "source_url",
    "source_retrieved_at",
)


def _decode_mixed_text(value: str) -> str:
    """Decode strings from the source's mixed Windows-1250/UTF-8 payload."""
    raw = value.encode("latin-1")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("windows-1250")


def _decode_value(value):
    if isinstance(value, str):
        return _decode_mixed_text(value)
    if isinstance(value, list):
        return [_decode_value(item) for item in value]
    if isinstance(value, dict):
        return {
            _decode_mixed_text(key): _decode_value(item)
            for key, item in value.items()
        }
    return value


def decode_source(payload: bytes) -> list[dict]:
    raw_records = json.loads(payload.decode("latin-1"))
    return [_decode_value(record) for record in raw_records]


def load_project_station_codes(alias_path: Path) -> set[int]:
    with alias_path.open(encoding="utf-8", newline="") as source:
        return {int(row["station_code"]) for row in csv.DictReader(source)}


def _normalize_partial_date(value, *, period_end: bool) -> str:
    text = str(value).strip()
    if not text:
        return ""
    if len(text) == 4 and text.isdigit():
        year = int(text)
        return (
            date(year - 1, 12, 31).isoformat()
            if period_end
            else date(year, 1, 1).isoformat()
        )
    return date.fromisoformat(text).isoformat()


def normalize_records(
    records: list[dict],
    station_codes: set[int],
    retrieved_at: date,
) -> list[dict]:
    normalized = []
    for record in records:
        raw_code = record["kod 9-znakowy"]
        if raw_code == "":
            continue

        station_code = int(raw_code)
        if station_code not in station_codes:
            continue

        normalized.append(
            {
                "station_code": station_code,
                "official_station_name": record["nazwa stacji"].upper(),
                "valid_from": _normalize_partial_date(
                    record["data_od"],
                    period_end=False,
                ),
                "valid_to": _normalize_partial_date(
                    record["data_do"],
                    period_end=True,
                ),
                "station_type": record["rodzaj stacji"],
                "data_rank": record["rząd danych w CBDH"],
                "latitude": str(record["latitude"]).replace(",", "."),
                "longitude": str(record["longitude"]).replace(",", "."),
                "elevation_m": record["wysokość [m npm]"],
                "metadata_status": "official",
                "source_url": SOURCE_URL,
                "source_retrieved_at": retrieved_at.isoformat(),
            }
        )

    official_records = sorted(
        normalized,
        key=lambda row: (row["station_code"], row["valid_from"]),
    )
    return _add_unavailable_periods(official_records, retrieved_at)


def _add_unavailable_periods(
    official_records: list[dict],
    retrieved_at: date,
) -> list[dict]:
    by_station = defaultdict(list)
    for record in official_records:
        by_station[record["station_code"]].append(record)

    timeline = []
    for station_code, station_records in by_station.items():
        for index, record in enumerate(station_records):
            timeline.append(record)
            valid_to = record["valid_to"]
            if not valid_to:
                continue

            gap_start = date.fromisoformat(valid_to) + timedelta(days=1)
            next_record = (
                station_records[index + 1]
                if index + 1 < len(station_records)
                else None
            )
            if next_record:
                next_start = date.fromisoformat(next_record["valid_from"])
                if gap_start >= next_start:
                    continue
                gap_end = next_start - timedelta(days=1)
            else:
                gap_end = None

            timeline.append(
                {
                    "station_code": station_code,
                    "official_station_name": "",
                    "valid_from": gap_start.isoformat(),
                    "valid_to": gap_end.isoformat() if gap_end else "",
                    "station_type": "",
                    "data_rank": "",
                    "latitude": "",
                    "longitude": "",
                    "elevation_m": "",
                    "metadata_status": "unavailable",
                    "source_url": SOURCE_URL,
                    "source_retrieved_at": retrieved_at.isoformat(),
                }
            )

    return sorted(
        timeline,
        key=lambda row: (row["station_code"], row["valid_from"]),
    )


def write_snapshot(records: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--aliases",
        type=Path,
        default=Path("postgresql_db/station_alias.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("postgresql_db/station_metadata_history.csv"),
    )
    parser.add_argument(
        "--retrieved-at",
        type=date.fromisoformat,
        default=date.today(),
    )
    parser.add_argument(
        "--source-file",
        type=Path,
        help="Use a previously downloaded source payload instead of HTTP.",
    )
    args = parser.parse_args()

    if args.source_file:
        payload = args.source_file.read_bytes()
    else:
        response = requests.get(SOURCE_URL, timeout=30)
        response.raise_for_status()
        payload = response.content

    station_codes = load_project_station_codes(args.aliases)
    records = normalize_records(
        decode_source(payload),
        station_codes,
        args.retrieved_at,
    )
    if {row["station_code"] for row in records} != station_codes:
        raise ValueError("IMGW metadata does not cover every project station code")

    write_snapshot(records, args.output)
    print(f"Wrote {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
