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
    
    def _get_last_searched_id(self, car_id: int) -> int | None:
        stmt = select(CarModel.last_checked_id).where(CarModel.id == car_id)
        last_checked_id = self.db.execute(stmt).scalar_one_or_none()
        return last_checked_id
        
    async def parse(self):
        # TODO: refactor this gigantic function to be many small ones
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
            # FINDING LAST CHECKED AD
            last_checked_id = self._get_last_searched_id(car_id)
            car_page_bazos = AutoPage(**args)
            car_ads = car_page_bazos.get_advertisements()
            car_ads = list(map(lambda ad: AutoAdvertisementPage(ad), car_ads))
            car_ads_ids = [e.id for e in car_ads]
            while (last_checked_id and last_checked_id not in car_ads_ids):
                car_page_bazos.go_next_page()
                car_ads = car_page_bazos.get_advertisements()
                car_ads = list(map(lambda ad: AutoAdvertisementPage(ad), car_ads))
                car_ads_ids = [e.id for e in car_ads]
            # PARCING ALL THE NEW ADDS
            if not last_checked_id: 
                queue_to_check = car_ads
            else:
                idx_of_last_checked_add = next(i for i, e in enumerate(car_ads) if e.id == last_checked_id)
                queue_to_check = car_ads[:idx_of_last_checked_add]
                while (car_page_bazos.go_previous_page()):
                    car_ads = car_page_bazos.get_advertisements()
                    car_ads = list(map(lambda ad: AutoAdvertisementPage(ad), car_ads))
                    queue_to_check.append(car_ads)
            await asyncio.gather(*(car_ad.get_page_text() for car_ad in queue_to_check))
            pass
            # TODO: Here implement going through queue and sending ad if it fits to any search and then save the new last checked id of the ad
