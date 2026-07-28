from unittest.mock import Mock, call

import pytest

from etl_process.etl_pipeline import ETLPipeline


def test_pipeline_loads_reference_data_before_refresh():
    pipeline = object.__new__(ETLPipeline)
    pipeline.db = Mock()

    steps = Mock()
    pipeline._load_reference_data = steps.load_reference_data
    pipeline._collect_files = steps.collect_files
    pipeline._parse_files = steps.parse_files
    pipeline._load_to_db = steps.load_to_db
    pipeline._refresh_db = steps.refresh_db
    steps.collect_files.return_value = ["weather.csv"]
    steps.parse_files.return_value = {"weather": Mock()}

    pipeline.run()

    assert steps.mock_calls == [
        call.load_reference_data(),
        call.collect_files(),
        call.parse_files(["weather.csv"]),
        call.load_to_db(steps.parse_files.return_value),
        call.refresh_db(),
    ]
    pipeline.db.disconnect.assert_called_once_with()


def test_refresh_error_is_not_suppressed():
    pipeline = object.__new__(ETLPipeline)
    pipeline.db = Mock()
    pipeline.db.exec_procedure.side_effect = RuntimeError("refresh failed")

    with pytest.raises(RuntimeError, match="refresh failed"):
        pipeline._refresh_db()
