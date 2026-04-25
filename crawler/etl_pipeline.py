import logging
from typing import Dict, List

from crawler_service import CrawlerService
from download_service import DownloadService
from schema_loader import SchemaLoader
from zip_extractor import ZipExtractor
from parser import Parser
from postgres_client import PostgresClient
from config import (
    get_db_config,
    get_dataset_config,
    get_dataset_schema_config,
)


logger = logging.getLogger(__name__)


class ETLPipeline:
    def __init__(self):
        self.db = self._init_db()
        self.dataset_config = get_dataset_config()
        self.dataset_schema_config = self._sort_schema_config()

        self.crawler = CrawlerService(self.dataset_config['url'])
        self.downloader = DownloadService()
        self.extractor = ZipExtractor()
        self.schema_loader = SchemaLoader()
        self.parser = Parser(self.dataset_schema_config, self.schema_loader)

    def _init_db(self) -> PostgresClient:
        db_config = get_db_config()
        db = PostgresClient(**db_config)
        db.connect()
        logger.info("Connected to database")
        return db

    def _sort_schema_config(self) -> Dict:
        config = get_dataset_schema_config()
        sorted_config = dict(
            sorted(
                config.items(),
                key=lambda x: len(x[1]["prefix"]),
                reverse=True
            )
        )
        return sorted_config

    def run(self):
        logger.info("ETL pipeline started")

        try:
            files = self._collect_files()
            dataframes = self._parse_files(files)
            self._load_to_db(dataframes)

            logger.info("ETL pipeline finished successfully")

        except Exception:
            logger.exception("ETL pipeline failed")
            raise

    def _collect_files(self) -> List[str]:
        logger.info("Starting crawl phase")

        all_files = []
        files_dict = self.crawler.crawl()

        logger.info(f"Crawler returned {len(files_dict)} sources")

        for source_name, dataset in files_dict.items():
            logger.info(f"Processing source: {source_name}")

            for file in dataset.files:
                try:
                    logger.debug(f"Downloading file: {file.url}")

                    zip_path = self.downloader.download(file.url)
                    extracted_files = self.extractor.extract(zip_path)

                    logger.debug(f"Extracted {len(extracted_files)} files from {file.url}")

                    all_files.extend(extracted_files)

                except Exception:
                    logger.exception(f"Failed processing file: {file.url}")

        logger.info(f"Collected total files: {len(all_files)}")
        return all_files

    def _parse_files(self, files: List[str]) -> Dict[str, "DataFrame"]:
        logger.info("Parsing files into dataframes")
        dataframes = self.parser.parse(files)
        logger.info(f"Parsed {len(dataframes)} datasets")
        return dataframes

    def _load_to_db(self, dataframes: Dict[str, "DataFrame"]):
        logger.info("Starting DB load phase")

        for key, df in dataframes.items():
            table_name = key

            try:
                logger.info(f"Uploading dataset: {key} -> {table_name}")
                logger.debug(f"Rows: {len(df)}")

                self.db.upload_dataframe(df, table_name)

                logger.info(f"Successfully loaded: {key}")

            except Exception:
                logger.exception(f"Failed loading dataset: {key}")
