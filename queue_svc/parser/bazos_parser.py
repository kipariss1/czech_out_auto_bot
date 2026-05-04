import asyncio
import logging

from src.database_utils import db_handler
from sqlalchemy import select, distinct, func
from src.models.models import CarSearch, CarModel, AdQueue
from queue_svc.bazos_api.auto_bazos_api import AutoPage, AutoAdvertisementPage, AutoPageSearchArgs


logger = logging.getLogger(__name__)


class BazosParser:

    def __init__(self):
        self.db = db_handler.get_db_connection()

    
    def _get_searches(self) -> list[CarSearch]:
        return list(self.db.query(CarSearch).all())
    
    def _get_price_range_for_car(self, car_id: int) -> tuple[int, int]:
        min_has_none = (
            self.db.query(CarSearch)
            .filter(CarSearch.car_model_id == car_id, CarSearch.price_range_from.is_(None))
            .first()
        )
        max_has_none = (
            self.db.query(CarSearch)
            .filter(CarSearch.car_model_id == car_id, CarSearch.price_range_to.is_(None))
            .first()
        )
        if min_has_none and max_has_none:
            return None, None   # type: ignore
        max_to = (
                self.db.query(func.max(CarSearch.price_range_to))
                .filter(CarSearch.car_model_id == car_id)
                .scalar()
            )
        min_from = (
            self.db.query(func.min(CarSearch.price_range_from))
            .filter(CarSearch.car_model_id == car_id)
            .scalar()
        )
        if min_has_none:
            return 0, max_to
        if max_has_none:
            return min_from, 0  
        return min_from, max_to
    
    async def _find_last_valid_checked_id(self, car: CarModel) -> str | None:
        if not car.last_checked_links:
            logger.debug("No checked ad history for car_model_id=%s", car.id)
            return None
        ad = None
        for el in car.last_checked_links:
            ad = AutoAdvertisementPage(el)
            if not await ad.is_deleted():
                logger.debug(
                    "Found last valid checked ad car_model_id=%s ad_id=%s",
                    car.id,
                    ad.id,
                )
                break
            logger.debug(
                "Skipping deleted checked ad car_model_id=%s link=%s",
                car.id,
                el,
            )
        return ad.id    # type: ignore
    
    async def _go_to_last_checked_id(self, car: CarModel, car_page_bazos: AutoPage) -> tuple[str | None, list[AutoAdvertisementPage]]:
        last_checked_id = await self._find_last_valid_checked_id(car)
        car_ads = car_page_bazos.get_advertisements()
        car_ads = list(map(lambda ad: AutoAdvertisementPage(ad), car_ads))
        car_ads_ids = [e.id for e in car_ads]
        logger.debug(
            "Loaded Bazos page car_model_id=%s page=%s ads=%s last_checked_id=%s",
            car.id,
            car_page_bazos.page,
            len(car_ads),
            last_checked_id,
        )
        while (last_checked_id and last_checked_id not in car_ads_ids):
            logger.info(
                "Last checked ad is not on current page; loading next page car_model_id=%s last_checked_id=%s current_page=%s",
                car.id,
                last_checked_id,
                car_page_bazos.page,
            )
            car_page_bazos.go_next_page()
            car_ads = car_page_bazos.get_advertisements()
            car_ads = list(map(lambda ad: AutoAdvertisementPage(ad), car_ads))
            car_ads_ids = [e.id for e in car_ads]
            logger.debug(
                "Loaded Bazos page car_model_id=%s page=%s ads=%s",
                car.id,
                car_page_bazos.page,
                len(car_ads),
            )
        page_with_last_checked_id = car_ads
        logger.info(
            "Resolved parser starting point car_model_id=%s page=%s last_checked_id=%s ads_on_page=%s",
            car.id,
            car_page_bazos.page,
            last_checked_id,
            len(page_with_last_checked_id),
        )
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
        action = "updated" if row else "created"
        if row:
            row.queue = links   # type: ignore
        else:
            row = AdQueue(
                car_model_id=car_id,
                queue=links
            )
            self.db.add(row)
        self.db.commit()
        logger.info(
            "Stored parser queue car_model_id=%s ads=%s action=%s",
            car_id,
            len(links),
            action,
        )

    async def _process_toped_ads(self, queue: list[AutoAdvertisementPage], car: CarModel) -> list[str]:
        if not car.last_checked_toped_links:
            logger.debug(
                "No topped ad history for car_model_id=%s; keeping queue unchanged ads=%s",
                car.id,
                len(queue),
            )
            return queue            # type: ignore
        is_toped_mask = await asyncio.gather(*[el.is_toped() for el in queue])
        toped = [el for el, is_toped in zip(queue, is_toped_mask) if is_toped]
        not_toped = [el for el, is_toped in zip(queue, is_toped_mask) if not is_toped]
        new_toped = [
            el for el in toped
            if el.link not in car.last_checked_toped_links
        ]
        logger.info(
            "Processed topped ads car_model_id=%s ads=%s topped=%s skipped_seen_topped=%s queued=%s",
            car.id,
            len(queue),
            len(toped),
            len(toped) - len(new_toped),
            len(new_toped) + len(not_toped),
        )
        return new_toped + not_toped    # type: ignore

        
    async def parse(self):
        logger.info("Parser run started")
        unique_car_searches_query = select(distinct(CarSearch.car_model_id))
        unique_car_ids = self.db.execute(unique_car_searches_query).scalars().all()
        logger.info("Parser found car models with searches count=%s", len(unique_car_ids))
        for car_id in unique_car_ids:
            try:
                car = self.db.query(CarModel).filter(CarModel.id == car_id).first()
                min_from, max_to = self._get_price_range_for_car(car_id)
                logger.info(
                    "Parsing car model car_model_id=%s model=%s %s price_from=%s price_to=%s",
                    car_id,
                    car.manufacturer,  # type: ignore
                    car.model,  # type: ignore
                    min_from,
                    max_to,
                )
                args: AutoPageSearchArgs = {
                    'model': f"{car.manufacturer} {car.model}", # type: ignore
                    'locality': None,
                    'range': None,
                    'price_from': min_from,
                    'price_to': max_to
                }
                car_page_bazos = AutoPage(**args)                           # type: ignore
                last_checked_id, page_with_last_checked_id = await self._go_to_last_checked_id(car, car_page_bazos)
                queue_to_check = self._form_queue_to_check(car_page_bazos, last_checked_id, page_with_last_checked_id)
                logger.info(
                    "Formed parser queue car_model_id=%s ads=%s last_checked_id=%s",
                    car_id,
                    len(queue_to_check),
                    last_checked_id,
                )
                queue_to_check = await self._process_toped_ads(queue_to_check, car)
                self._add_queue_to_db(car_id, queue_to_check)             # type: ignore
            except Exception:
                logger.exception("Parser failed for car_model_id=%s", car_id)
                raise
        logger.info("Parser run finished")
        logger.info("+" + "-" * 30 + "+")

