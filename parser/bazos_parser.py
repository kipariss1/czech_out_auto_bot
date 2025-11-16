import asyncio
from src.database_utils import db_handler
from sqlalchemy import select, distinct
from src.models.models import CarSearch, CarModel
from bazos_api.auto_bazos_api import AutoPage, AutoAdvertisementPage, AutoPageSearchArgs


class BazosParser:

    def __init__(self):
        self.db = db_handler.get_db_connection()

    
    def _get_searches(self) -> list[CarSearch]:
        return list(self.db.query(CarSearch).all())
    
    async def parse(self):
        unique_car_searches_query = select(distinct(CarSearch.car_model_id))
        unique_car_ids = self.db.execute(unique_car_searches_query).scalars().all()
        # TODO: get lowest price_from and highest price_to to limit the ads by that 
        for car_id in unique_car_ids:
            # TODO: here use bazos API to get the page and parse all the new advertisements
            car = self.db.query(CarModel).filter(CarModel.id == car_id).first()
            # TODO: maybe kindof refactor the args
            args: AutoPageSearchArgs = {
                'model': f"{car.manufacturer} {car.model}",
                'locality': None,
                'range': None,
                'price_from': None,
                'price_to': None
            }
            car_page_bazos = AutoPage(**args)
            car_ads = car_page_bazos.get_advertisements()
            car_ads = map(lambda ad: AutoAdvertisementPage(ad), car_ads)
            await asyncio.gather(*(car_ad.get_page_text() for car_ad in car_ads))
