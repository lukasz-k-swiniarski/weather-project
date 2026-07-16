import pytest

from etl_process.config import get_dataset_config, get_db_config

DB_ENV = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "weather_db",
    "DB_USER": "postgres",
    "DB_PASSWORD": "test-password",
    "DB_SCHEMA": "layer_bronze",
}


def test_dataset_config_is_loaded_independently_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    config = get_dataset_config()

    assert config["url"].startswith("https://")


def test_db_config_reads_required_environment(monkeypatch):
    for key, value in DB_ENV.items():
        monkeypatch.setenv(key, value)

    config = get_db_config()

    assert config["port"] == 5432
    assert config["schema"] == "layer_bronze"
    assert "password" in config


def test_db_config_reports_missing_values(monkeypatch):
    monkeypatch.setattr("etl_process.config.load_dotenv", lambda *args, **kwargs: None)
    for key in DB_ENV:
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(RuntimeError, match="DB_HOST"):
        get_db_config()
