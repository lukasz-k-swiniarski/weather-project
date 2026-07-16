import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
REQUIRED_DB_ENV_VARS = (
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_SCHEMA",
)


def get_db_config():
    load_dotenv(PROJECT_DIR / ".env")
    load_dotenv(PACKAGE_DIR / ".env")
    missing = [name for name in REQUIRED_DB_ENV_VARS if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Missing required database environment variables: " + ", ".join(missing)
        )

    try:
        port = int(os.environ["DB_PORT"])
    except ValueError as exc:
        raise RuntimeError("DB_PORT must be an integer") from exc

    return {
        "host": os.environ["DB_HOST"],
        "port": port,
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "schema": os.environ["DB_SCHEMA"],
        "if_exists": "replace",
        "chunksize": 1000,
    }

def get_dataset_config(path: str | Path = PACKAGE_DIR / "config_dataset_synop_1.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_dataset_schema_config(
    path: str | Path = PACKAGE_DIR / "config_dataset_synop_1_schema.yaml",
):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
