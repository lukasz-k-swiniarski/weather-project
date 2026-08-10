from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

from etl_process.reference_data_loader import ReferenceDataLoader

VALID_ALIAS = {
    "station_name": ["WARSZAWA-OKĘCIE"],
    "station_code": [352200375],
    "location_id": ["LOC001"],
}
VALID_LOCATION = {
    "location_id": ["LOC001"],
    "location_name": ["WARSZAWA"],
    "location_type": ["miasto"],
    "voivodeship": ["mazowieckie"],
}
VALID_METADATA = {
    "station_code": [352200375],
    "official_station_name": ["WARSZAWA-OKĘCIE"],
    "valid_from": ["1951-01-01"],
    "valid_to": [None],
    "station_type": ["synoptyczna"],
    "data_rank": ["synop"],
    "latitude": [52.166667],
    "longitude": [20.966667],
    "elevation_m": [106],
    "metadata_status": ["official"],
    "source_url": ["https://example.test/stations.json"],
    "source_retrieved_at": ["2026-07-28"],
}


def _write_reference_files(
    tmp_path,
    aliases=VALID_ALIAS,
    locations=VALID_LOCATION,
    metadata=VALID_METADATA,
):
    alias_path = tmp_path / "station_alias.csv"
    location_path = tmp_path / "station_reporting_location.csv"
    metadata_path = tmp_path / "station_metadata_history.csv"
    pd.DataFrame(aliases).to_csv(alias_path, index=False)
    pd.DataFrame(locations).to_csv(location_path, index=False)
    pd.DataFrame(metadata).to_csv(metadata_path, index=False)
    return alias_path, location_path, metadata_path


def test_load_station_reference_data_replaces_silver_tables(tmp_path):
    paths = _write_reference_files(tmp_path)
    db = Mock()

    counts = ReferenceDataLoader(db, *paths).load_station_reference_data()

    assert counts == {
        "station_alias": 1,
        "station_reporting_location": 1,
        "station_metadata_history": 1,
    }
    tables = db.replace_tables_data.call_args.args[0]
    assert set(tables) == set(counts)
    assert db.replace_tables_data.call_args.kwargs == {"schema": "layer_silver"}


def test_rejects_unknown_reporting_location(tmp_path):
    aliases = VALID_ALIAS | {"location_id": ["LOC999"]}
    paths = _write_reference_files(tmp_path, aliases=aliases)

    with pytest.raises(ValueError, match="unknown reporting locations"):
        ReferenceDataLoader(Mock(), *paths).load_station_reference_data()


def test_rejects_invalid_voivodeship(tmp_path):
    locations = VALID_LOCATION | {"voivodeship": ["unknown"]}
    paths = _write_reference_files(tmp_path, locations=locations)

    with pytest.raises(ValueError, match="invalid voivodeships"):
        ReferenceDataLoader(Mock(), *paths).load_station_reference_data()


def test_rejects_overlapping_metadata_periods(tmp_path):
    metadata = {
        column: values * 2
        for column, values in VALID_METADATA.items()
    }
    metadata["valid_from"] = ["1951-01-01", "2000-01-01"]
    metadata["valid_to"] = [None, None]
    paths = _write_reference_files(tmp_path, metadata=metadata)

    with pytest.raises(ValueError, match="open metadata period"):
        ReferenceDataLoader(Mock(), *paths).load_station_reference_data()


def test_rejects_incomplete_metadata_code_coverage(tmp_path):
    aliases = {
        "station_name": ["WARSZAWA-OKĘCIE", "KRAKÓW-BALICE"],
        "station_code": [352200375, 350190566],
        "location_id": ["LOC001", "LOC001"],
    }
    paths = _write_reference_files(tmp_path, aliases=aliases)

    with pytest.raises(ValueError, match="cover exactly"):
        ReferenceDataLoader(Mock(), *paths).load_station_reference_data()


def test_rejects_uncovered_metadata_period(tmp_path):
    metadata = {
        column: values * 2
        for column, values in VALID_METADATA.items()
    }
    metadata["valid_from"] = ["1951-01-01", "2000-01-01"]
    metadata["valid_to"] = ["1999-01-01", None]
    paths = _write_reference_files(tmp_path, metadata=metadata)

    with pytest.raises(ValueError, match="uncovered validity periods"):
        ReferenceDataLoader(Mock(), *paths).load_station_reference_data()


def test_committed_reporting_locations_cover_boundary_cases():
    project_root = Path(__file__).parents[1]
    locations = pd.read_csv(
        project_root / "postgresql_db" / "station_reporting_location.csv"
    ).set_index("location_name")

    expected = {
        "BIELSKO-BIAŁA": "śląskie",
        "WIELUŃ": "łódzkie",
        "PIŁA": "wielkopolskie",
        "CHOJNICE": "pomorskie",
        "OLSZTYN": "warmińsko-mazurskie",
        "MIKOŁAJKI": "warmińsko-mazurskie",
        "USTKA": "pomorskie",
        "KĘTRZYN": "warmińsko-mazurskie",
    }

    assert locations.loc[list(expected), "voivodeship"].to_dict() == expected
    assert locations["voivodeship"].nunique() == 16
