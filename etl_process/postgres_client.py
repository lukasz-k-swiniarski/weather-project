import logging

import pandas as pd
from sqlalchemy import URL, create_engine, text

logger = logging.getLogger(__name__)

class PostgresClient:
    def __init__(self, host, port, dbname, user, password, schema, if_exists, chunksize):
        self.host = host
        self.schema = schema
        self.if_exists = if_exists
        self.chunksize = chunksize
        self.connection_url = URL.create(
            drivername="postgresql+psycopg2",
            username=user,
            password=password,
            host=host,
            port=port,
            database=dbname,
        )
        self.engine = None

    def connect(self):
        logger.info("Connecting to PostgreSQL database")
        self.engine = create_engine(self.connection_url, pool_pre_ping=True)
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Successfully connected to PostgreSQL database")

    def disconnect(self):
        if self.engine:
            self.engine.dispose()

    def upload_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
    ):
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        df.to_sql(
            name=table_name,
            con=self.engine,
            schema=self.schema,
            if_exists=self.if_exists,
            index=False,
            chunksize=self.chunksize,
            method="multi"  # batch insert
        )

    def replace_table_data(
        self,
        df: pd.DataFrame,
        table_name: str,
        schema: str | None = None,
    ) -> None:
        if self.engine is None:
            raise RuntimeError("Database connection has not been initialized")

        target_schema = schema or self.schema
        with self.engine.begin() as connection:
            connection.execute(text(f'DELETE FROM "{target_schema}"."{table_name}"'))
            df.to_sql(
                name=table_name,
                con=connection,
                schema=target_schema,
                if_exists="append",
                index=False,
                chunksize=self.chunksize,
                method="multi",
            )

    def exec_procedure(
        self,
        proc_name: str
    ):
        if self.engine is None:
            raise RuntimeError("Database connection has not been initialized")

        with self.engine.connect() as conn:
            conn.execute(text(f'CALL {self.schema}.{proc_name}()'))
            conn.commit()
