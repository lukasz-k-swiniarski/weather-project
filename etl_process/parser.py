import logging
import os
from pathlib import Path

import pandas as pd

from etl_process.schema_loader import SchemaLoader

logger = logging.getLogger(__name__)


class Parser:
    def __init__(self, dataset_config: dict, schema_loader: SchemaLoader):
        self.dataset_config = dataset_config
        self.schema_loader = schema_loader

    def _match_dataset(self, filename: str) -> str | None:
        datasets_by_prefix_length = sorted(
            self.dataset_config.items(),
            key=lambda item: len(item[1]["prefix"]),
            reverse=True,
        )
        for dataset_name, config in datasets_by_prefix_length:
            if filename.startswith(config["prefix"]):
                return dataset_name
        return None

    def _read_file(
        self,
        path: str,
        dataset_name: str,
        columns: list[str],
        encoding: str,
        expected_column_count: int,
    ) -> pd.DataFrame:
        try:
            dataframe = pd.read_csv(path, header=None, encoding=encoding)
        except Exception as exc:
            raise ValueError(
                f"Failed to read {dataset_name} source file {path}: {exc}"
            ) from exc

        if dataframe.empty:
            raise ValueError(f"Source file is empty: {path}")

        actual_column_count = len(dataframe.columns)
        if actual_column_count != expected_column_count:
            raise ValueError(
                f"Invalid column count in {path}: expected "
                f"{expected_column_count}, got {actual_column_count}"
            )

        dataframe.columns = columns
        return dataframe

    def _validate_dataset(
        self,
        dataset_name: str,
        dataframe: pd.DataFrame,
        grain: list[str],
    ) -> None:
        missing_grain_columns = [
            column for column in grain if column not in dataframe.columns
        ]
        if missing_grain_columns:
            raise ValueError(
                f"Dataset {dataset_name} is missing grain columns: "
                + ", ".join(missing_grain_columns)
            )

        null_grain = dataframe[grain].isna().any(axis=1)
        if null_grain.any():
            raise ValueError(
                f"Dataset {dataset_name} contains {int(null_grain.sum())} "
                "rows with an incomplete grain"
            )

        dates = pd.to_datetime(
            {
                "year": dataframe["rok"],
                "month": dataframe["mc"],
                "day": dataframe["dz"],
            },
            errors="coerce",
        )
        invalid_dates = dates.isna()
        if invalid_dates.any():
            raise ValueError(
                f"Dataset {dataset_name} contains {int(invalid_dates.sum())} "
                "rows with an invalid observation date"
            )

        duplicate_grain = dataframe.duplicated(subset=grain, keep=False)
        if duplicate_grain.any():
            duplicate_key_count = (
                dataframe.loc[duplicate_grain, grain].drop_duplicates().shape[0]
            )
            raise ValueError(
                f"Dataset {dataset_name} contains {duplicate_key_count} "
                "duplicated grain keys"
            )

        logger.info(
            "Validated %s: rows=%s, date_range=%s..%s",
            dataset_name,
            len(dataframe),
            dates.min().date(),
            dates.max().date(),
        )

    def _validate_dataset_relationships(
        self,
        dataframes: dict[str, pd.DataFrame],
    ) -> None:
        for dataset_name, config in self.dataset_config.items():
            parent_name = config.get("key_subset_of")
            if not parent_name:
                continue

            child = dataframes[dataset_name]
            parent = dataframes[parent_name]
            grain = config["grain"]
            child_keys = pd.MultiIndex.from_frame(child[grain])
            parent_keys = pd.MultiIndex.from_frame(parent[grain])
            orphan_keys = child_keys.difference(parent_keys)

            if not orphan_keys.empty:
                raise ValueError(
                    f"Dataset {dataset_name} contains {len(orphan_keys)} grain "
                    f"keys missing from {parent_name}"
                )

            missing_child_keys = parent_keys.difference(child_keys)
            if not missing_child_keys.empty:
                logger.warning(
                    "%s does not cover %s of %s grain keys",
                    dataset_name,
                    len(missing_child_keys),
                    parent_name,
                )

    def parse(self, file_paths: list[str]) -> dict[str, pd.DataFrame]:
        grouped_files = {key: [] for key in self.dataset_config}

        for path in file_paths:
            filename = os.path.basename(path)
            dataset_name = self._match_dataset(filename)
            if dataset_name:
                grouped_files[dataset_name].append(path)
            else:
                logger.warning("No dataset match for file: %s", filename)

        result = {}
        for dataset_name, paths in grouped_files.items():
            dataset_config = self.dataset_config[dataset_name]
            if not paths:
                if dataset_config.get("required", False):
                    raise ValueError(
                        f"No source files found for required dataset: {dataset_name}"
                    )
                logger.warning("No files for optional dataset: %s", dataset_name)
                continue

            schema_config = dataset_config["schema"]
            columns = self.schema_loader.load_columns(schema_config)
            expected_column_count = dataset_config["expected_column_count"]
            if len(columns) != expected_column_count:
                raise ValueError(
                    f"Contract mismatch for {dataset_name}: expected_column_count "
                    f"is {expected_column_count}, but {len(columns)} columns are defined"
                )

            dataframes = []
            for path in paths:
                filename = Path(path).name
                if not filename.startswith(dataset_config["prefix"]):
                    raise ValueError(
                        f"File {path} does not match prefix "
                        f"{dataset_config['prefix']} for {dataset_name}"
                    )
                dataframes.append(
                    self._read_file(
                        path=path,
                        dataset_name=dataset_name,
                        columns=columns,
                        encoding=schema_config["encoding"],
                        expected_column_count=expected_column_count,
                    )
                )

            dataframe = pd.concat(dataframes, ignore_index=True)
            self._validate_dataset(
                dataset_name=dataset_name,
                dataframe=dataframe,
                grain=dataset_config["grain"],
            )
            result[dataset_name] = dataframe

        self._validate_dataset_relationships(result)
        return result
