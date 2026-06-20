import asyncio
import logging

from src.database_utils import db_handler
from src.models.models import AdQueue, CarSearch
from queue_svc.bazos_api.auto_bazos_api import (
    AutoAdvertisementPage,
    AutoPage,
    AutoPageSearchArgs,
)


logger = logging.getLogger(__name__)


class BazosParser:

    def __init__(self, page_limit_for_new_search: int = 30):
        self.db = db_handler.get_db_connection()
        self.page_limit_for_new_search = page_limit_for_new_search

    def _get_searches(self) -> list[CarSearch]:
        return list(self.db.query(CarSearch).all())

    @staticmethod
    def _get_ads_from_current_page(car_page_bazos: AutoPage) -> list[AutoAdvertisementPage]:
        car_ads = car_page_bazos.get_advertisements()
        return list(map(lambda ad: AutoAdvertisementPage(ad), car_ads))

    @staticmethod
    def _is_new_search(search: CarSearch) -> bool:
        return not search.last_checked_links and not search.last_checked_toped_links

    @staticmethod
    def _get_history_links(search: CarSearch) -> list[str]:
        return (search.last_checked_links or []), (search.last_checked_toped_links or [])

    @staticmethod
    def _flatten_pages_from_oldest_to_newest(
        pages: list[list[AutoAdvertisementPage]],
    ) -> list[AutoAdvertisementPage]:
        queue_to_check: list[AutoAdvertisementPage] = []
        for ads in reversed(pages):
            queue_to_check.extend(reversed(ads))
        return queue_to_check

    @staticmethod
    def _build_search_args(search: CarSearch) -> AutoPageSearchArgs:
        car = search.car_model
        locality = search.psc_code
        return {
            "model": f"{car.manufacturer} {car.model}",
            "locality": locality,
            "range": search.psc_km_range if locality else None,
            "price_from": search.price_range_from,
            "price_to": search.price_range_to,
        }  # type: ignore

    async def _find_last_valid_checked_id(self, search: CarSearch) -> str | None:
        async def find_not_deleted_in_(history: list[str]) -> str | None:
            # last_checked_links and last_checked_toped_links are written oldest to newest
            for link in reversed(history):
                ad = AutoAdvertisementPage(link)
                if not await ad.is_deleted():
                    logger.debug(
                        "Found last valid checked ad search_id=%s ad_id=%s",
                        search.id,
                        ad.id,
                    )
                    return ad.id
                logger.debug(
                    "Skipping deleted checked ad search_id=%s link=%s",
                    search.id,
                    link,
                )

        history_links, history_toped_links = self._get_history_links(search)
        if not history_links and not history_toped_links:
            logger.debug("No checked ad history for search_id=%s", search.id)
            return None
        valid_link = await find_not_deleted_in_(history_links)
        valid_toped_link = await find_not_deleted_in_(history_toped_links)
        return valid_link or valid_toped_link

    def _collect_all_pages(
        self,
        car_page_bazos: AutoPage,
        search: CarSearch,
    ) -> list[list[AutoAdvertisementPage]]:
        pages: list[list[AutoAdvertisementPage]] = []
        while True:
            car_ads = self._get_ads_from_current_page(car_page_bazos)
            pages.append(car_ads)
            logger.debug(
                "Loaded Bazos page search_id=%s page=%s ads=%s",
                search.id,
                car_page_bazos.page,
                len(car_ads),
            )
            if not car_page_bazos.go_next_page():
                return pages
            if car_page_bazos.page >= self.page_limit_for_new_search:
                return pages
            logger.info(
                "Search has older Bazos page; loading next page search_id=%s next_page=%s",
                search.id,
                car_page_bazos.page,
            )

    async def _collect_pages_until_last_checked(
        self,
        search: CarSearch,
        car_page_bazos: AutoPage,
    ) -> tuple[str | None, list[list[AutoAdvertisementPage]], list[AutoAdvertisementPage]]:
        last_checked_id = await self._find_last_valid_checked_id(search)
        if not last_checked_id:
            pages = self._collect_all_pages(car_page_bazos, search)
            return None, pages, []
        pages: list[list[AutoAdvertisementPage]] = []
        while True:
            car_ads = self._get_ads_from_current_page(car_page_bazos)
            pages.append(car_ads)
            car_ads_ids = [e.id for e in car_ads]
            logger.debug(
                "Loaded Bazos page search_id=%s page=%s ads=%s last_checked_id=%s",
                search.id,
                car_page_bazos.page,
                len(car_ads),
                last_checked_id,
            )
            if last_checked_id in car_ads_ids:
                return last_checked_id, pages, car_ads
            logger.info(
                "Last checked ad is not on current page; loading next page search_id=%s last_checked_id=%s current_page=%s",
                search.id,
                last_checked_id,
                car_page_bazos.page,
            )
            if not car_page_bazos.go_next_page():
                logger.warning(
                    "Last checked ad was not found on available pages; falling back to full queue search_id=%s last_checked_id=%s current_page=%s",
                    search.id,
                    last_checked_id,
                    car_page_bazos.page,
                )
                return None, pages, car_ads
            if car_page_bazos.page >= self.page_limit_for_new_search:
                logger.info(
                    "Hit the limit of pages, while going back searching for last checked add search_id=%s last_checked_id=%s current_page=%s",
                    search.id,
                    last_checked_id,
                    car_page_bazos.page,
                )
                return pages

    def _form_queue_for_existing_search(
        self,
        last_checked_id: str | None,
        pages: list[list[AutoAdvertisementPage]],
        page_with_last_checked_id: list[AutoAdvertisementPage],
    ) -> list[AutoAdvertisementPage]:
        if not last_checked_id:
            return self._flatten_pages_from_oldest_to_newest(pages)

        idx_of_last_checked_ad = next(
            i for i, ad in enumerate(page_with_last_checked_id)
            if ad.id == last_checked_id
        )
        queue_pages = pages[:-1] + [page_with_last_checked_id[:idx_of_last_checked_ad]]
        return self._flatten_pages_from_oldest_to_newest(queue_pages)

    def _form_queue_for_new_search(
        self,
        car_page_bazos: AutoPage,
        search: CarSearch,
    ) -> list[AutoAdvertisementPage]:
        pages = self._collect_all_pages(car_page_bazos, search)
        return self._flatten_pages_from_oldest_to_newest(pages)

    def _add_queue_to_db(self, search_id: int, queue_to_check: list[AutoAdvertisementPage]):
        links = [e.link for e in queue_to_check]
        row = self.db.query(AdQueue).filter_by(car_search_id=search_id).one_or_none()
        action = "updated" if row else "created"
        if row:
            row.queue = links  # type: ignore
        else:
            row = AdQueue(
                car_search_id=search_id,
                queue=links,
            )
            self.db.add(row)
        self.db.commit()
        logger.info(
            "Stored parser queue search_id=%s ads=%s action=%s",
            search_id,
            len(links),
            action,
        )

    async def parse(self):
        logger.info("Parser run started")
        searches = self._get_searches()
        logger.info("Parser found searches count=%s", len(searches))
        for search in searches:
            try:
                car = search.car_model
                logger.info(
                    "Parsing search search_id=%s car_model_id=%s model=%s %s price_from=%s price_to=%s locality=%s range=%s",
                    search.id,
                    search.car_model_id,
                    car.manufacturer,
                    car.model,
                    search.price_range_from,
                    search.price_range_to,
                    search.psc_code,
                    search.psc_km_range,
                )
                car_page_bazos = AutoPage(**self._build_search_args(search))
                if self._is_new_search(search):
                    queue_to_check = self._form_queue_for_new_search(
                        car_page_bazos,
                        search,
                    )
                    last_checked_id = None
                else:
                    (
                        last_checked_id,
                        pages,
                        page_with_last_checked_id,
                    ) = await self._collect_pages_until_last_checked(
                        search,
                        car_page_bazos,
                    )
                    queue_to_check = self._form_queue_for_existing_search(
                        last_checked_id,
                        pages,
                        page_with_last_checked_id,
                    )

                logger.info(
                    "Formed parser queue search_id=%s ads=%s last_checked_id=%s",
                    search.id,
                    len(queue_to_check),
                    last_checked_id,
                )
                self._add_queue_to_db(search.id, queue_to_check)
            except Exception:
                logger.exception("Parser failed for search_id=%s", search.id)
                raise
        logger.info("Parser run finished")
        logger.info("+" + "-" * 30 + "+")
