from pathlib import Path

import pandas as pd


class ReferenceDataLoader:
    ALIAS_COLUMNS = ("station_name", "station_code", "location_id")
    LOCATION_COLUMNS = (
        "location_id",
        "location_name",
        "location_type",
        "voivodeship",
    )
    METADATA_COLUMNS = (
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
    VOIVODESHIPS = {
        "dolnośląskie",
        "kujawsko-pomorskie",
        "lubelskie",
        "lubuskie",
        "łódzkie",
        "małopolskie",
        "mazowieckie",
        "opolskie",
        "podkarpackie",
        "podlaskie",
        "pomorskie",
        "śląskie",
        "świętokrzyskie",
        "warmińsko-mazurskie",
        "wielkopolskie",
        "zachodniopomorskie",
    }

    def __init__(
        self,
        db,
        alias_path: str | Path,
        location_path: str | Path,
        metadata_path: str | Path,
        target_schema: str = "layer_silver",
    ):
        self.db = db
        self.alias_path = Path(alias_path)
        self.location_path = Path(location_path)
        self.metadata_path = Path(metadata_path)
        self.target_schema = target_schema

    def load_station_reference_data(self) -> dict[str, int]:
        aliases = self._read_csv(self.alias_path, self.ALIAS_COLUMNS)
        locations = self._read_csv(self.location_path, self.LOCATION_COLUMNS)
        metadata = self._read_csv(self.metadata_path, self.METADATA_COLUMNS)

        self._validate_aliases(aliases)
        self._validate_locations(locations)
        self._validate_metadata(metadata)
        self._validate_relationships(aliases, locations, metadata)

        aliases["station_code"] = aliases["station_code"].astype("int64")
        metadata["station_code"] = metadata["station_code"].astype("int64")
        metadata["valid_from"] = pd.to_datetime(
            metadata["valid_from"]
        ).dt.date
        metadata["valid_to"] = pd.to_datetime(
            metadata["valid_to"]
        ).dt.date
        metadata["source_retrieved_at"] = pd.to_datetime(
            metadata["source_retrieved_at"]
        ).dt.date
        tables = {
            "station_reporting_location": locations,
            "station_metadata_history": metadata,
            "station_alias": aliases,
        }
        self.db.replace_tables_data(tables, schema=self.target_schema)
        return {table_name: len(dataframe) for table_name, dataframe in tables.items()}

    @staticmethod
    def _read_csv(path: Path, required_columns: tuple[str, ...]) -> pd.DataFrame:
        if not path.is_file():
            raise FileNotFoundError(f"Reference file does not exist: {path}")

        dataframe = pd.read_csv(path, encoding="utf-8")
        actual_columns = tuple(dataframe.columns)
        if actual_columns != required_columns:
            raise ValueError(
                f"Invalid columns in {path.name}. "
                f"Expected {required_columns}, got {actual_columns}"
            )

        missing = [
            column
            for column in required_columns
            if dataframe[column].isna().any()
            and column
            not in {
                "official_station_name",
                "valid_to",
                "station_type",
                "data_rank",
                "latitude",
                "longitude",
                "elevation_m",
            }
        ]
        if missing:
            raise ValueError(
                f"{path.name} contains missing required values in: "
                + ", ".join(missing)
            )
        return dataframe

    @staticmethod
    def _numeric_column(dataframe: pd.DataFrame, column: str) -> pd.Series:
        values = pd.to_numeric(dataframe[column], errors="coerce")
        if values.isna().any():
            raise ValueError(f"Reference data contains invalid {column} values")
        return values

    def _validate_aliases(self, aliases: pd.DataFrame) -> None:
        aliases["station_code"] = self._numeric_column(aliases, "station_code")
        if aliases["station_name"].duplicated().any():
            raise ValueError("Station aliases must have unique station_name values")

        locations_per_code = aliases.groupby("station_code")["location_id"].nunique()
        if locations_per_code.gt(1).any():
            raise ValueError("A station code cannot map to multiple reporting locations")

    def _validate_locations(self, locations: pd.DataFrame) -> None:
        if locations["location_id"].duplicated().any():
            raise ValueError("Reporting locations must have unique location_id values")
        if locations["location_name"].duplicated().any():
            raise ValueError("Reporting locations must have unique location_name values")

        invalid = set(locations["voivodeship"]) - self.VOIVODESHIPS
        if invalid:
            raise ValueError(
                "Reporting locations contain invalid voivodeships: "
                + ", ".join(sorted(invalid))
            )
    def _validate_metadata(self, metadata: pd.DataFrame) -> None:
        metadata["station_code"] = self._numeric_column(metadata, "station_code")
        for column in ("latitude", "longitude", "elevation_m"):
            metadata[column] = pd.to_numeric(metadata[column], errors="coerce")

        official = metadata["metadata_status"].eq("official")
        unavailable = metadata["metadata_status"].eq("unavailable")
        if not (official | unavailable).all():
            raise ValueError("Station metadata contains an invalid metadata_status")
        official_required = (
            "official_station_name",
            "station_type",
            "latitude",
            "longitude",
            "elevation_m",
        )
        if metadata.loc[official, list(official_required)].isna().any().any():
            raise ValueError("Official station metadata contains missing values")
        if metadata.loc[
            unavailable,
            ["latitude", "longitude", "elevation_m"],
        ].notna().any().any():
            raise ValueError(
                "Unavailable metadata periods cannot contain inferred geography"
            )

        if not metadata.loc[official, "latitude"].between(48.5, 55.5).all():
            raise ValueError("Station metadata contains latitude outside Poland")
        if not metadata.loc[official, "longitude"].between(13.5, 24.5).all():
            raise ValueError("Station metadata contains longitude outside Poland")

        valid_from = pd.to_datetime(metadata["valid_from"], errors="coerce")
        valid_to = pd.to_datetime(metadata["valid_to"], errors="coerce")
        retrieved_at = pd.to_datetime(
            metadata["source_retrieved_at"],
            errors="coerce",
        )
        if valid_from.isna().any() or retrieved_at.isna().any():
            raise ValueError("Station metadata contains invalid dates")
        if (valid_to.notna() & valid_to.lt(valid_from)).any():
            raise ValueError("Station metadata contains an invalid validity period")
        if metadata.duplicated(["station_code", "valid_from"]).any():
            raise ValueError(
                "Station metadata must be unique by station_code and valid_from"
            )

        periods = metadata.assign(
            valid_from=valid_from,
            valid_to=valid_to,
        ).sort_values(["station_code", "valid_from"])
        previous_end = periods.groupby("station_code")["valid_to"].shift()
        if (previous_end.isna() & periods.groupby("station_code").cumcount().gt(0)).any():
            raise ValueError("An open metadata period must be the latest period")
        if (previous_end.notna() & periods["valid_from"].le(previous_end)).any():
            raise ValueError("Station metadata contains overlapping validity periods")
        expected_start = previous_end + pd.Timedelta(days=1)
        if (
            previous_end.notna()
            & periods["valid_from"].ne(expected_start)
        ).any():
            raise ValueError(
                "Station metadata timeline contains uncovered validity periods"
            )

        latest_periods = periods.groupby("station_code").tail(1)
        if latest_periods["valid_to"].notna().any():
            raise ValueError(
                "Every station metadata timeline must end with an open period"
            )

    @staticmethod
    def _validate_relationships(
        aliases: pd.DataFrame,
        locations: pd.DataFrame,
        metadata: pd.DataFrame,
    ) -> None:
        unknown_locations = set(aliases["location_id"]) - set(
            locations["location_id"]
        )
        if unknown_locations:
            raise ValueError(
                "Aliases reference unknown reporting locations: "
                + ", ".join(sorted(unknown_locations))
            )

        alias_codes = set(aliases["station_code"])
        metadata_codes = set(metadata["station_code"])
        if alias_codes != metadata_codes:
            raise ValueError(
                "Station metadata must cover exactly the station codes "
                "present in station aliases"
            )
