import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, Session
from src.models.models import Base
import os


class SqliteDBHandler:

    __DB_NAME = "local.db"
    __DB_URL = "sqlite:///./local.db"

    def __init__(self, dbname: str = None):
        if dbname:
            self.__DB_NAME = dbname
            self.__DB_URL = f"sqlite:///./{dbname}"
        self._engine = sa.create_engine(self.__DB_URL)
        self._sessionmaker = sessionmaker
        self._db_conn = None
        Base.metadata.create_all(bind=self._engine)

    def __get_db_session(self) -> Session:
        return self._sessionmaker(bind=self._engine)

    def _get_db_connection(self) -> Session:
        sess = self.__get_db_session()
        db_conn = sess()
        return db_conn

    def get_db_connection(self) -> Session:
        if self._db_conn is None:
            self._db_conn = self._get_db_connection()
        return self._db_conn

    def close_db_connection(self) -> bool:
        if self._db_conn:
            self._db_conn.close()
            return True
        return False

    def __del__(self):
        if os.path.exists(self.__DB_NAME):
            os.remove(self.__DB_NAME)
