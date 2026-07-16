from unittest.mock import Mock

import pandas as pd
import pytest

from etl_process.reference_data_loader import ReferenceDataLoader

VALID_MAPPING = {
    "station_name": ["WARSZAWA"],
    "location": ["miasto"],
    "location_name": ["WARSZAWA"],
    "id": ["LOC001"],
    "station_code": [352200375],
}


def test_load_station_mapping_replaces_silver_table(tmp_path):
    mapping_path = tmp_path / "mapping.csv"
    pd.DataFrame(VALID_MAPPING).to_csv(mapping_path, index=False)
    db = Mock()

    row_count = ReferenceDataLoader(db, mapping_path).load_station_mapping()

    assert row_count == 1
    dataframe, table_name = db.replace_table_data.call_args.args
    assert table_name == "synop_location_mapp"
    assert dataframe.to_dict(orient="list") == VALID_MAPPING
    assert db.replace_table_data.call_args.kwargs == {"schema": "layer_silver"}


def test_load_station_mapping_rejects_missing_required_value(tmp_path):
    mapping_path = tmp_path / "mapping.csv"
    invalid_mapping = VALID_MAPPING | {"station_name": [None]}
    pd.DataFrame(invalid_mapping).to_csv(mapping_path, index=False)

    with pytest.raises(ValueError, match="station_name"):
        ReferenceDataLoader(Mock(), mapping_path).load_station_mapping()


def test_load_station_mapping_rejects_inconsistent_location_ids(tmp_path):
    mapping_path = tmp_path / "mapping.csv"
    invalid_mapping = {
        "station_name": ["WARSZAWA", "WARSZAWA-OKĘCIE"],
        "location": ["miasto", "miasto"],
        "location_name": ["WARSZAWA", "WARSZAWA"],
        "id": ["LOC001", "LOC002"],
        "station_code": [352200375, 352200375],
    }
    pd.DataFrame(invalid_mapping).to_csv(mapping_path, index=False)

    with pytest.raises(ValueError, match="one-to-one"):
        ReferenceDataLoader(Mock(), mapping_path).load_station_mapping()
