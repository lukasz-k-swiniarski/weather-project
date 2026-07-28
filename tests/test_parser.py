from pathlib import Path

import pytest

from etl_process.parser import Parser
from etl_process.schema_loader import SchemaLoader


def dataset_config() -> dict:
    common_schema = {
        "encoding": "cp1250",
        "columns": ["nsp", "post", "rok", "mc", "dz"],
    }
    return {
        "daily": {
            "prefix": "s_d_",
            "required": True,
            "expected_column_count": 5,
            "grain": ["nsp", "rok", "mc", "dz"],
            "schema": common_schema,
        },
        "daily_secondary": {
            "prefix": "s_d_t_",
            "required": True,
            "expected_column_count": 5,
            "grain": ["nsp", "rok", "mc", "dz"],
            "key_subset_of": "daily",
            "schema": common_schema,
        },
    }


def write_source(path: Path, rows: list[str]) -> str:
    path.write_text("\n".join(rows), encoding="cp1250")
    return str(path)


def make_parser() -> Parser:
    return Parser(dataset_config(), SchemaLoader())


def test_parser_loads_required_datasets_with_secondary_key_subset(tmp_path):
    primary = write_source(
        tmp_path / "s_d_primary.csv",
        ["1,WARSZAWA,2024,1,1", "1,WARSZAWA,2024,1,2"],
    )
    secondary = write_source(
        tmp_path / "s_d_t_secondary.csv",
        ["1,WARSZAWA,2024,1,1"],
    )

    result = make_parser().parse([primary, secondary])

    assert len(result["daily"]) == 2
    assert len(result["daily_secondary"]) == 1


def test_parser_rejects_missing_required_dataset(tmp_path):
    primary = write_source(
        tmp_path / "s_d_primary.csv",
        ["1,WARSZAWA,2024,1,1"],
    )

    with pytest.raises(ValueError, match="daily_secondary"):
        make_parser().parse([primary])


def test_parser_rejects_invalid_column_count(tmp_path):
    primary = write_source(
        tmp_path / "s_d_primary.csv",
        ["1,WARSZAWA,2024,1"],
    )
    secondary = write_source(
        tmp_path / "s_d_t_secondary.csv",
        ["1,WARSZAWA,2024,1,1"],
    )

    with pytest.raises(ValueError, match="Invalid column count"):
        make_parser().parse([primary, secondary])


def test_parser_rejects_invalid_observation_date(tmp_path):
    primary = write_source(
        tmp_path / "s_d_primary.csv",
        ["1,WARSZAWA,2024,2,30"],
    )
    secondary = write_source(
        tmp_path / "s_d_t_secondary.csv",
        ["1,WARSZAWA,2024,2,30"],
    )

    with pytest.raises(ValueError, match="invalid observation date"):
        make_parser().parse([primary, secondary])


def test_parser_rejects_incomplete_grain(tmp_path):
    primary = write_source(
        tmp_path / "s_d_primary.csv",
        [",WARSZAWA,2024,1,1"],
    )
    secondary = write_source(
        tmp_path / "s_d_t_secondary.csv",
        ["1,WARSZAWA,2024,1,1"],
    )

    with pytest.raises(ValueError, match="incomplete grain"):
        make_parser().parse([primary, secondary])


def test_parser_rejects_duplicate_grain(tmp_path):
    primary = write_source(
        tmp_path / "s_d_primary.csv",
        ["1,WARSZAWA,2024,1,1", "1,WARSZAWA,2024,1,1"],
    )
    secondary = write_source(
        tmp_path / "s_d_t_secondary.csv",
        ["1,WARSZAWA,2024,1,1"],
    )

    with pytest.raises(ValueError, match="duplicated grain keys"):
        make_parser().parse([primary, secondary])


def test_parser_rejects_secondary_key_without_primary_match(tmp_path):
    primary = write_source(
        tmp_path / "s_d_primary.csv",
        ["1,WARSZAWA,2024,1,1"],
    )
    secondary = write_source(
        tmp_path / "s_d_t_secondary.csv",
        ["1,WARSZAWA,2024,1,2"],
    )

    with pytest.raises(ValueError, match="missing from daily"):
        make_parser().parse([primary, secondary])


def test_parser_fails_when_source_file_cannot_be_read(tmp_path):
    primary = write_source(
        tmp_path / "s_d_primary.csv",
        ["1,WARSZAWA,2024,1,1"],
    )
    missing_secondary = tmp_path / "s_d_t_missing.csv"

    with pytest.raises(ValueError, match="Failed to read"):
        make_parser().parse([primary, str(missing_secondary)])
