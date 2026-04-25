from sqlalchemy import create_engine
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class PostgresClient:
    def __init__(self, host, port, dbname, user, password, schema, if_exists, chunksize):
        self.host = host
        self.schema = schema
        self.if_exists = if_exists
        self.chunksize = chunksize
        self.connection_string = (
            f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
        )
        self.engine = None

    def connect(self):
        logger.info('connecting to PostgreSQL database')
        try:
            self.engine = create_engine(self.connection_string)
            logger.info('successfully connected to PostgreSQL database')
        except Exception as e:
            logger.debug(e)

    def disconnect(self):
        if self.engine:
            self.engine.dispose()

    def upload_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
    ):
        df.to_sql(
            name=table_name,
            con=self.engine,
            schema=self.schema,
            if_exists=self.if_exists,
            index=False,
            chunksize=self.chunksize,
            method="multi"  # batch insert
        )

