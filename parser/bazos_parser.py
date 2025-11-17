import asyncio
from src.database_utils import db_handler
from sqlalchemy import select, distinct, func
from src.models.models import CarSearch, CarModel
from bazos_api.auto_bazos_api import AutoPage, AutoAdvertisementPage, AutoPageSearchArgs


class BazosParser:

    def __init__(self):
        self.db = db_handler.get_db_connection()

    
    def _get_searches(self) -> list[CarSearch]:
        return list(self.db.query(CarSearch).all())
    
    def _get_price_range_for_car(self, car_id: int) -> dict[str, int]:
        min_from = (
            self.db.query(func.min(CarSearch.price_range_from))
            .filter(CarSearch.car_model_id == car_id)
            .scalar()
        )
        max_to = (
            self.db.query(func.max(CarSearch.price_range_to))
            .filter(CarSearch.car_model_id == car_id)
            .scalar()
        )
        return min_from, max_to
    
    async def parse(self):
        unique_car_searches_query = select(distinct(CarSearch.car_model_id))
        unique_car_ids = self.db.execute(unique_car_searches_query).scalars().all()
        for car_id in unique_car_ids:
            car = self.db.query(CarModel).filter(CarModel.id == car_id).first()
            min_from, max_to = self._get_price_range_for_car(car_id)
            args: AutoPageSearchArgs = {
                'model': f"{car.manufacturer} {car.model}",
                'locality': None,
                'range': None,
                'price_from': min_from,
                'price_to': max_to
            }
            car_page_bazos = AutoPage(**args)
            car_ads = car_page_bazos.get_advertisements()
            car_ads = list(map(lambda ad: AutoAdvertisementPage(ad), car_ads))
            await asyncio.gather(*(car_ad.get_page_text() for car_ad in car_ads))
            # TODO: here implement logic of remembering which is last checked ad and going from there
