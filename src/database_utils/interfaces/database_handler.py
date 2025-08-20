from abc import ABC, abstractmethod
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from src import SRC_DIR
from src.models.models import CarModel
import pandas as pd

class DatabaseHandler(ABC):

    def __init__(self, Base):
        self._engine = self.init_engine()
        self._db_conn = None
        Base.metadata.create_all(bind=self._engine)

    @staticmethod
    @abstractmethod
    def db_url() -> str:
        pass

    def init_engine(self):
        return sa.create_engine(self.db_url())

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
    
    def _cars_loaded(self) -> bool:
        db = self.get_db_connection()
        return db.query(CarModel).count() > 0
    
    def updload_cars_to_db(self):
        db = self.get_db_connection()
        if (SRC_DIR / "db" / "cars.csv").exists() and not self._cars_loaded():
            csv = pd.read_csv(SRC_DIR / "db" / "cars.csv")
            for _, row in csv.iterrows():
                new_car = CarModel(manufacturer=row['Manufacturer'], model=row['Model'])
                db.add(new_car)
                db.commit()