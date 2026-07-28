from unittest.mock import Mock

import pandas as pd

from etl_process.postgres_client import PostgresClient


def test_upload_dataframe_replaces_data_without_replacing_table():
    client = object.__new__(PostgresClient)
    client.schema = "layer_bronze"
    client.replace_table_data = Mock()
    dataframe = pd.DataFrame({"Station Code": [1]})

    client.upload_dataframe(dataframe, "weather")

    assert dataframe.columns.tolist() == ["station_code"]
    client.replace_table_data.assert_called_once_with(
        dataframe,
        "weather",
        schema="layer_bronze",
    )
