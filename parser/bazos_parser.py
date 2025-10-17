from src.database_utils import db_handler
from sqlalchemy import select, distinct
from src.models.models import CarSearch
import requests


class BazosParser:

    def __init__(self):
        self.db = db_handler.get_db_connection()

    
    def _get_searches(self) -> list[CarSearch]:
        return list(self.db.query(CarSearch).all())
    
    def parse(self):
        unique_car_searches_query = select(distinct(CarSearch.car_model_id))
        unique_car_ids = self.db.execute(unique_car_searches_query).scalars().all()
        for car_id in unique_car_ids:
            # TODO: here use bazos API to get the page and parse all the new advertisements
            pass
