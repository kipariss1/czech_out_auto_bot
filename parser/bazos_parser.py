from src.database_utils import db_handler
from sqlalchemy import select, distinct, func
from src.models.models import CarSearch, CarModel, AdQueue
from parser.bazos_api.auto_bazos_api import AutoPage, AutoAdvertisementPage, AutoPageSearchArgs


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
    
    def _go_to_last_checked_id(self, car: CarModel, car_page_bazos: AutoPage) -> tuple[str | None, list[AutoAdvertisementPage]]:
        last_checked_id = str(car.last_checked_id)
        car_ads = car_page_bazos.get_advertisements()
        car_ads = list(map(lambda ad: AutoAdvertisementPage(ad), car_ads))
        car_ads_ids = [e.id for e in car_ads]
        while (last_checked_id and last_checked_id not in car_ads_ids):
            car_page_bazos.go_next_page()
            car_ads = car_page_bazos.get_advertisements()
            car_ads = list(map(lambda ad: AutoAdvertisementPage(ad), car_ads))
            car_ads_ids = [e.id for e in car_ads]
        page_with_last_checked_id = car_ads
        return last_checked_id, page_with_last_checked_id
    
    def _form_queue_to_check(self, car_page_bazos: AutoPage, last_checked_id: str | None, page_with_last_checked_id: list[AutoAdvertisementPage]) -> list[AutoAdvertisementPage]:
        if not last_checked_id: 
                queue_to_check = page_with_last_checked_id
        else:
            idx_of_last_checked_add = next(i for i, e in enumerate(page_with_last_checked_id) if e.id == last_checked_id)
            queue_to_check = page_with_last_checked_id[:idx_of_last_checked_add]
            while (car_page_bazos.go_previous_page()):
                car_ads = car_page_bazos.get_advertisements()
                car_ads = list(map(lambda ad: AutoAdvertisementPage(ad), car_ads))
                queue_to_check = car_ads + queue_to_check
        return queue_to_check
    
    def _add_queue_to_db(self, car_id: str, queue_to_check: list[AutoAdvertisementPage]):
        links = [e.link for e in queue_to_check]
        row = self.db.query(AdQueue).filter_by(car_model_id=car_id).one_or_none()
        if row:
            row.queue = links
        else:
            row = AdQueue(
                car_model_id=car_id,
                queue=links
            )
            self.db.add(row)
        self.db.commit()
        
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
            last_checked_id, page_with_last_checked_id = self._go_to_last_checked_id(car, car_page_bazos)
            queue_to_check = self._form_queue_to_check(car_page_bazos, last_checked_id, page_with_last_checked_id)
            self._add_queue_to_db(car_id, queue_to_check)            


