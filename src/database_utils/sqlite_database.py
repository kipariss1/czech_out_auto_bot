from src.settings.settings import settings
import sqlalchemy as sa
import pandas as pd
from sqlalchemy.orm import sessionmaker, Session
from src.models.models import Base, CarModel
from src import SRC_DIR


class SqliteDBHandler:

    __DB_URL = settings.db_url

    def __init__(self, dbname: str = None):
        if dbname:
            self.__DB_URL = f"sqlite:///../db/{dbname}.db"
        self._engine = sa.create_engine(self.__DB_URL)
        self._sessionmaker = sessionmaker
        self._db_conn = None
        Base.metadata.create_all(bind=self._engine)

    def updload_cars_to_db(self):
        db = self.get_db_connection()
        if (SRC_DIR / "db" / "cars.csv").exists():
            csv = pd.read_csv(SRC_DIR / "db" / "cars.csv")
            for _, row in csv.iterrows():
                new_car = CarModel(manufacturer=row['Manufacturer'], model=row['Model'])
                db.add(new_car)
                db.commit()


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
