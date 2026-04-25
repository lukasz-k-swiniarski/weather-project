import logging

from etl_pipeline import ETLPipeline
from logging_config import setup_logging

if __name__ == "__main__":
    setup_logging(log_file="etl.log")
    logger = logging.getLogger(__name__)

    logger.info("============== PROCESS START ========================")
    pipeline = ETLPipeline()
    pipeline.run()
    logger.info("============== PROCESS END ==========================")
