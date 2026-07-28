import pytest

from etl_process.schema_loader import SchemaLoader


def test_schema_loader_returns_normalized_versioned_columns():
    columns = SchemaLoader().load_columns({"columns": ["NSP", " POST "]})

    assert columns == ["nsp", "post"]


@pytest.mark.parametrize("columns", [None, [], ["nsp", "NSP"], ["nsp", " "]])
def test_schema_loader_rejects_invalid_columns(columns):
    with pytest.raises(ValueError):
        SchemaLoader().load_columns({"columns": columns})
