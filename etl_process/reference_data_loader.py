from pathlib import Path

import pandas as pd


class ReferenceDataLoader:
    REQUIRED_COLUMNS = (
        "station_name",
        "location",
        "location_name",
        "id",
        "station_code",
    )
    REQUIRED_VALUES = ("station_name", "location", "station_code")

    def __init__(
        self,
        db,
        mapping_path: str | Path,
        target_schema: str = "layer_silver",
    ):
        self.db = db
        self.mapping_path = Path(mapping_path)
        self.target_schema = target_schema

    def load_station_mapping(self) -> int:
        dataframe = self._read_station_mapping()
        self.db.replace_table_data(
            dataframe,
            "synop_location_mapp",
            schema=self.target_schema,
        )
        return len(dataframe)

    def _read_station_mapping(self) -> pd.DataFrame:
        if not self.mapping_path.is_file():
            raise FileNotFoundError(
                f"Station mapping file does not exist: {self.mapping_path}"
            )

        dataframe = pd.read_csv(self.mapping_path, encoding="utf-8")
        actual_columns = tuple(dataframe.columns)
        if actual_columns != self.REQUIRED_COLUMNS:
            raise ValueError(
                "Invalid station mapping columns. "
                f"Expected {self.REQUIRED_COLUMNS}, got {actual_columns}"
            )

        missing_values = [
            column
            for column in self.REQUIRED_VALUES
            if dataframe[column].isna().any()
        ]
        if missing_values:
            raise ValueError(
                "Station mapping contains missing required values in: "
                + ", ".join(missing_values)
            )

        station_codes = pd.to_numeric(dataframe["station_code"], errors="coerce")
        if station_codes.isna().any():
            raise ValueError("Station mapping contains invalid station_code values")

        dataframe["station_code"] = station_codes.astype("int64")
        return dataframe
