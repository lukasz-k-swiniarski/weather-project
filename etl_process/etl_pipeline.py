import logging

from pandas import DataFrame

from etl_process.config import (
    PROJECT_DIR,
    get_dataset_config,
    get_dataset_schema_config,
    get_db_config,
)
from etl_process.crawler_service import CrawlerService
from etl_process.download_service import DownloadService
from etl_process.parser import Parser
from etl_process.postgres_client import PostgresClient
from etl_process.reference_data_loader import ReferenceDataLoader
from etl_process.schema_loader import SchemaLoader
from etl_process.zip_extractor import ZipExtractor

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
        self.reference_loader = ReferenceDataLoader(
            self.db,
            PROJECT_DIR / "postgresql_db" / "station_alias.csv",
            PROJECT_DIR / "postgresql_db" / "station_reporting_location.csv",
            PROJECT_DIR / "postgresql_db" / "station_metadata_history.csv",
        )

    def _init_db(self) -> PostgresClient:
        db_config = get_db_config()
        db = PostgresClient(**db_config)
        db.connect()
        logger.info("Connected to database")
        return db

    def _sort_schema_config(self) -> dict:
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
            self._load_reference_data()
            files = self._collect_files()
            dataframes = self._parse_files(files)
            self._load_to_db(dataframes)
            self._refresh_db()

            logger.info("ETL pipeline finished successfully")

        except Exception:
            logger.exception("ETL pipeline failed")
            raise

        finally:
            self.db.disconnect()
            logger.info("Database connection closed")

    def _load_reference_data(self) -> None:
        logger.info("Loading station reference data")
        row_counts = self.reference_loader.load_station_reference_data()
        logger.info("Loaded station reference rows: %s", row_counts)

    def _collect_files(self) -> list[str]:
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

    def _parse_files(self, files: list[str]) -> dict[str, DataFrame]:
        logger.info("Parsing files into dataframes")
        dataframes = self.parser.parse(files)
        logger.info(f"Parsed {len(dataframes)} datasets")
        return dataframes

    def _load_to_db(self, dataframes: dict[str, DataFrame]):
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
                raise

    def _refresh_db(self):
        logger.info("Starting exec procedures...")
        try:
            self.db.exec_procedure('refresh_etl')
            logger.info("Procedures executed successfully")
        except Exception:
            logger.exception("Procedure execution failed")
            raise
