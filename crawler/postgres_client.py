from sqlalchemy import create_engine
import pandas as pd

class PostgresClient:
    def __init__(self, host, port, dbname, user, password):
        self.connection_string = (
            f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
        )
        self.engine = None

    def connect(self):
        self.engine = create_engine(self.connection_string)

    def disconnect(self):
        if self.engine:
            self.engine.dispose()

    def upload_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        schema: str = "public",
        if_exists: str = "replace",  # 'replace', 'append', 'fail'
        chunksize: int = 1000
    ):
        df.to_sql(
            name=table_name,
            con=self.engine,
            schema=schema,
            if_exists=if_exists,
            index=False,
            chunksize=chunksize,
            method="multi"  # batch insert
        )

