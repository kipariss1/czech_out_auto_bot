from src.database_utils.interfaces.database_handler import DatabaseHandler
from src import SRC_DIR, OS_NAME
import sqlalchemy as sa
from src.models.models import CarModel
import pandas as pd



class SqliteDBHandler(DatabaseHandler):

    @staticmethod
    def _db_url():
        return f"sqlite:////{(SRC_DIR / 'db' / 'local.db').as_posix()}" if OS_NAME == "Linux" else f"sqlite:///./src/db/local.db"
    
    def init_engine(self):
        return sa.create_engine(self._db_url())
    
    def updload_cars_to_db(self):
        db = self.get_db_connection()
        if (SRC_DIR / "db" / "cars.csv").exists() and not self._cars_loaded():
            csv = pd.read_csv(SRC_DIR / "db" / "cars.csv")
            for _, row in csv.iterrows():
                new_car = CarModel(manufacturer=row['Manufacturer'], model=row['Model'])
                db.add(new_car)
                db.commit()

