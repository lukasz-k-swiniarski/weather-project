import os
import pandas as pd
import logging

from schema_loader import SchemaLoader

logger = logging.getLogger(__name__)


class Parser:
    def __init__(self, dataset_config: dict, schema_loader: SchemaLoader):
        self.dataset_config = dataset_config
        self.schema_loader = schema_loader


    def _match_dataset(self, filename: str) -> str | None:
        for dataset_name, config in self.dataset_config.items():
            prefix = config.get("prefix")

            if filename.startswith(prefix):
                return dataset_name

        return None

    def parse(self, file_paths: list[str]) -> dict[str, pd.DataFrame]:
        grouped_files = {key: [] for key in self.dataset_config.keys()}

        # grupowanie plików
        for path in file_paths:
            filename = os.path.basename(path)

            dataset_name = self._match_dataset(filename)

            if dataset_name:
                grouped_files[dataset_name].append(path)
            else:
                logger.warning(f"No dataset match for file: {filename}")

        # wczytanie i łączenie
        result = {}

        for dataset_name, paths in grouped_files.items():
            if not paths:
                logger.warning(f"No files for dataset: {dataset_name}")
                continue

            dfs = []

            # pobranie schematu z configu
            schema_config = self.dataset_config[dataset_name].get("schema")
            columns = self.schema_loader.load_columns(schema_config)

            for path in paths:
                try:
                    encoding = schema_config.get("encoding")

                    df = pd.read_csv(path, header=None, encoding=encoding)
                    df.columns = columns

                    dfs.append(df)

                except Exception as e:
                    logger.error(f"Failed to read {path}: {e}")

            if dfs:
                result[dataset_name] = pd.concat(dfs, ignore_index=True)

        return result