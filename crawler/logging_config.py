import logging
import sys


def setup_logging(level=logging.INFO, log_file: str = None):
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # prevent duplicate handlers (important in reloads / notebooks)
    if root_logger.handlers:
        return

    # console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # optional file logging
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)