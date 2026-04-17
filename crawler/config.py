from dotenv import load_dotenv
import yaml
import os

def get_db_config():
    load_dotenv()
    return {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT")),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }

def get_dataset_config(path="config_dataset_synop_1.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_dataset_schema_config(path="config_dataset_synop_1_schema.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)