from unittest.mock import MagicMock, patch

from etl_process.logging_config import setup_logging


def test_logging_uses_utf8_for_console_and_file():
    root_logger = MagicMock(handlers=[])
    stdout = MagicMock()

    with (
        patch("etl_process.logging_config.logging.getLogger", return_value=root_logger),
        patch("etl_process.logging_config.logging.StreamHandler") as stream_handler,
        patch("etl_process.logging_config.logging.FileHandler") as file_handler,
        patch("etl_process.logging_config.sys.stdout", stdout),
    ):
        setup_logging(log_file="etl.log")

    stdout.reconfigure.assert_called_once_with(
        encoding="utf-8",
        errors="backslashreplace",
    )
    stream_handler.assert_called_once_with(stdout)
    file_handler.assert_called_once_with("etl.log", encoding="utf-8")
