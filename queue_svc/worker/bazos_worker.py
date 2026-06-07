import asyncio
import logging
from html import escape
from typing import Any

from src.database_utils import db_handler
from src.models.models import AdQueue, CarSearch, User
from queue_svc.bazos_api.auto_bazos_api import AutoAdvertisementPage
from queue_svc.ollama_api.ollama_client import OllamaClient, ValidCarAd
from telegram_bot import bot


logger = logging.getLogger(__name__)


class BazosWorker:

    def __init__(self):
        self.db = db_handler.get_db_connection()
        self.ollama = OllamaClient("gemma4:e4b")

    @staticmethod
    def _in_range(
        data: dict[str, Any],
        key: str,
        min_value: int | None,
        max_value: int | None,
    ) -> bool:
        try:
            element = int(data[key])
        except (KeyError, TypeError, ValueError):
            return True
        if min_value is not None and element < min_value:
            return False
        if max_value is not None and element > max_value:
            return False
        return True

    @staticmethod
    def _fits_to_search_criteria(car_parse_res: ValidCarAd, search: CarSearch) -> bool:
        car = search.car_model
        if car_parse_res["brand"] != car.manufacturer or car_parse_res["model"] != car.model:
            return False
        # TODO: here check if PSC and range fits as well
        return (
            BazosWorker._in_range(
                car_parse_res,
                "mileage",
                search.mileage_range_from,
                search.mileage_range_to,
            ) and
            BazosWorker._in_range(
                car_parse_res,
                "year",
                search.year_range_from,
                search.year_range_to,
            ) and
            BazosWorker._in_range(
                car_parse_res,
                "price",
                search.price_range_from,
                search.price_range_to,
            )
        )

    @staticmethod
    def _format_range(min_value: int | None, max_value: int | None, suffix: str = "") -> str:
        if min_value is None and max_value is None:
            return "any"
        if min_value is None:
            return f"<= {max_value}{suffix}"
        if max_value is None:
            return f">= {min_value}{suffix}"
        return f"{min_value} - {max_value}{suffix}"

    @staticmethod
    def _format_table(rows: list[tuple[str, str, str]]) -> str:
        header = ("Parameter", "Search", "Car")
        widths = [
            max(len(header[i]), *(len(row[i]) for row in rows))
            for i in range(len(header))
        ]
        lines = [
            " | ".join(header[i].ljust(widths[i]) for i in range(len(header))),
            "-+-".join("-" * width for width in widths),
        ]
        lines.extend(
            " | ".join(row[i].ljust(widths[i]) for i in range(len(row)))
            for row in rows
        )
        return "<pre>" + escape("\n".join(lines)) + "</pre>"

    def _build_comparison_table(self, search: CarSearch, car_parse_res: ValidCarAd) -> str:
        car = search.car_model
        rows = [
            ("Brand", car.manufacturer, str(car_parse_res.get("brand", "n/a"))),
            ("Model", car.model, str(car_parse_res.get("model", "n/a"))),
            (
                "Year",
                self._format_range(search.year_range_from, search.year_range_to),
                str(car_parse_res.get("year", "n/a")),
            ),
            (
                "Mileage",
                self._format_range(
                    search.mileage_range_from,
                    search.mileage_range_to,
                    " km",
                ),
                f"{car_parse_res.get('mileage', 'n/a')} km",
            ),
            (
                "Price",
                self._format_range(
                    search.price_range_from,
                    search.price_range_to,
                    " CZK",
                ),
                f"{car_parse_res.get('price', 'n/a')} CZK",
            ),
            ("Engine", "any", str(car_parse_res.get("engine", "n/a"))),
        ]
        return self._format_table(rows)

    def _send_new_ad_notification(
        self,
        search: CarSearch,
        ad: AutoAdvertisementPage,
        car_parse_res: ValidCarAd,
    ):
        car = search.car_model
        table = self._build_comparison_table(search, car_parse_res)
        message = f"""
🚨 <b>New car found!</b>

🏎️ <b>{escape(car.manufacturer)} {escape(car.model)}</b>

{table}

🔗 <a href="{escape(ad.link, quote=True)}">View advertisement</a>
"""
        user = self.db.query(User).filter(User.id == search.user_id).first()
        logger.info(
            "Sending new ad notification search_id=%s user_id=%s car_model_id=%s ad_id=%s",
            search.id,
            search.user_id,
            car.id,
            ad.id,
        )
        bot.send_message(
            chat_id=user.telegram_id,
            text=message,
            parse_mode="HTML",
        )

    @staticmethod
    async def _should_be_added_to_toped_history(
        ad: AutoAdvertisementPage,
        search: CarSearch,
    ):
        is_toped = await ad.is_toped()
        return is_toped and (
            not search.last_checked_toped_links
            or ad.link not in search.last_checked_toped_links
        )

    @staticmethod
    def _should_be_added_to_history(ad: AutoAdvertisementPage, search: CarSearch):
        if not search.last_checked_links:
            return True
        if ad.link not in search.last_checked_links:
            return True
        return False

    async def _add_checked_ad_to_history(
        self,
        ad: AutoAdvertisementPage,
        search: CarSearch,
    ):
        if await self._should_be_added_to_toped_history(ad, search):
            search.add_last_checked_toped_link(ad.link)
            self.db.commit()
            logger.debug(
                "Added topped ad to history search_id=%s ad_id=%s",
                search.id,
                ad.id,
            )
            return
        if self._should_be_added_to_history(ad, search):
            search.add_last_checked_link(ad.link)
            self.db.commit()
            logger.debug(
                "Added ad to history search_id=%s ad_id=%s",
                search.id,
                ad.id,
            )
            return

    async def _was_already_checked(self, ad: AutoAdvertisementPage, search: CarSearch) -> bool:
        if await ad.is_toped():
            return ad.link in (search.last_checked_toped_links or [])
        return ad.link in (search.last_checked_links or [])

    async def _process_row_in_queue(self, row: AdQueue):
        queue = row.queue or []
        search = (
            self.db.query(CarSearch)
            .filter(CarSearch.id == row.car_search_id)
            .first()
        )
        if search is None:
            logger.warning(
                "Skipping worker queue because search no longer exists car_search_id=%s",
                row.car_search_id,
            )
            return

        car = search.car_model
        ads = list(map(lambda el: AutoAdvertisementPage(el), queue))
        logger.info(
            "Processing worker queue search_id=%s car_model_id=%s ads=%s",
            search.id,
            search.car_model_id,
            len(ads),
        )
        await asyncio.gather(*[ad.get_page_text() for ad in ads])
        for ad in ads:
            if await self._was_already_checked(ad, search):
                logger.info(
                    "Skipping already checked ad search_id=%s ad_id=%s",
                    search.id,
                    ad.id,
                )
                queue.remove(ad.link)
                row.queue = queue
                self.db.commit()
                continue
            logger.debug(
                "Processing ad with Ollama search_id=%s car_model_id=%s ad_id=%s ad_link=%s",
                search.id,
                car.id,
                ad.id,
                ad.link,
            )
            res = self.ollama.process(ad_text=ad.text, car=car)
            await self._add_checked_ad_to_history(ad, search)
            queue.remove(ad.link)
            row.queue = queue
            self.db.commit()
            if res["is_valid_ad"]:
                logger.info(
                    "Ollama marked ad as valid search_id=%s car_model_id=%s ad_id=%s ad_link=%s",
                    search.id,
                    car.id,
                    ad.id,
                    ad.link,
                )
                res["price"] = str(ad.price)
                logger.debug(
                    "Ad parse result search_id=%s car_model_id=%s ad_id=%s ad_link=%s parse_res=%s",
                    search.id,
                    car.id,
                    ad.id,
                    ad.link,
                    res,
                )
                if self._fits_to_search_criteria(res, search):
                    self._send_new_ad_notification(search, ad, res)
                else:
                    logger.info(
                        "Valid ad did not match search search_id=%s car_model_id=%s ad_id=%s ad_link=%s",
                        search.id,
                        car.id,
                        ad.id,
                        ad.link,
                    )
            else:
                logger.debug(
                    "Ollama marked ad as invalid search_id=%s car_model_id=%s ad_id=%s ad_link=%s",
                    search.id,
                    car.id,
                    ad.id,
                    ad.link,
                )
        logger.info(
            "Finished worker queue search_id=%s remaining_ads=%s",
            search.id,
            len(queue),
        )

    async def process_queue(self):
        logger.info("Worker run started")
        queue_rows = (
            self.db.query(AdQueue)
            .filter(AdQueue.queue.isnot(None))
            .all()
        )
        logger.info("Worker found queue rows count=%s", len(queue_rows))
        for row in queue_rows:
            try:
                await self._process_row_in_queue(row)
            except Exception:
                logger.exception(
                    "Worker failed for car_search_id=%s",
                    row.car_search_id,
                )
                raise
        logger.info("Worker run finished")
        logger.info("+" + "-" * 30 + "+")
