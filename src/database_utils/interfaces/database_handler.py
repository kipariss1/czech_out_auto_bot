from abc import ABC, abstractmethod
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

class DatabaseHandler(ABC):

    def __init__(self, Base):
        self._engine = self.init_engine()
        self._db_conn = None
        Base.metadata.create_all(bind=self._engine)

    @abstractmethod
    def init_engine(self) -> Engine:
        pass

    def __get_db_session(self) -> Session:
        return sessionmaker(bind=self._engine)

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