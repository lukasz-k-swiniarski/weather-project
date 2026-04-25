import pandas as pd
import logging

logger = logging.getLogger(__name__)


class SchemaLoader:
    def __init__(self):
        self._cache = {}  # key: path → value: columns list

    def load_columns(self, schema_config: dict) -> list[str]:
        source = schema_config.get("source")
        path = schema_config.get("path")
        encoding = schema_config.get("encoding")

        if not path:
            raise ValueError("Schema config must contain 'path'")

        # CACHE HIT
        if path in self._cache:
            logger.info(f"Schema cache hit: {path}")
            return self._cache[path]

        # LOAD
        try:
            logger.info(f"Loading schema from: {path}")

            if source in ("url", "file"):
                df = pd.read_csv(path, encoding=encoding)
            else:
                raise ValueError(f"Unsupported schema source: {source}")

            columns = df.columns.tolist()

            # SAVE TO CACHE
            self._cache[path] = columns

            return columns

        except Exception as e:
            logger.error(f"Failed to load schema from {path}: {e}")
            raise