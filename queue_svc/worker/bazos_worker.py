from src.database_utils import db_handler
from src.models.models import AdQueue, CarModel, CarSearch, User
from queue_svc.bazos_api.auto_bazos_api import AutoAdvertisementPage
from queue_svc.ollama_api.ollama_client import OllamaClient, ValidCarAd
from telegram_bot import bot
from typing import Any
import asyncio

class BazosWorker:
    
    def __init__(self):
        self.db = db_handler.get_db_connection()
        self.ollama = OllamaClient()

    @staticmethod
    def _in_range(data: dict[str, Any], key: str, min_value: int, max_value: int) -> bool:
        try:
            element = int(data[key])
        except (KeyError, TypeError):
            return True
        return min_value < element < max_value

    @staticmethod
    def _fits_to_search_criteria(car_parse_res: ValidCarAd, search: CarSearch, car: CarModel) -> bool:
        if car_parse_res['brand'] != car.manufacturer or car_parse_res['model'] != car.model:
            return False
        # TODO: here check if PSC and range fits as well
        return (
            BazosWorker._in_range(car_parse_res, 'mileage', search.mileage_range_from, search.mileage_range_to) and
            BazosWorker._in_range(car_parse_res, 'year', search.year_range_from, search.year_range_to) and
            BazosWorker._in_range(car_parse_res, 'price', search.price_range_from, search.price_range_to)
        )
    
    def _send_new_ad_notification(self, search: CarSearch, ad: AutoAdvertisementPage, car: CarModel):
        attrs = search.to_dict()['attributes']
        message = f"""
🚨 <b>New car found!</b>

🏎️ <b>{car.manufacturer} {car.model}</b>

<b>Search criteria:</b>
• Year: {attrs.get('Year range', '—')}
• Mileage: {attrs.get('Mileage range', '—')}
• Price: {attrs.get('Price range', '—')}

🔗 <a href="{ad.link}">View advertisement</a>
"""
        user = self.db.query(User).filter(User.id == search.user_id).first()
        bot.send_message(
            chat_id=user.telegram_id,
            text=message,
            parse_mode="HTML",
        )

    @staticmethod
    async def _should_be_added_to_toped_history(ad: AutoAdvertisementPage, car: CarModel):
        if await ad.is_toped() and not car.last_checked_toped_links:
            return True
        if await ad.is_toped() and ad.link not in car.last_checked_toped_links:
            return True
        return False
    
    @staticmethod
    def _should_be_added_to_history(ad: AutoAdvertisementPage, car: CarModel):
        if not car.last_checked_links:
            return True
        if ad.link not in car.last_checked_links:
            return True
        return False

    async def _add_checked_ad_to_history(self, ad: AutoAdvertisementPage, car: CarModel):
        if await self._should_be_added_to_toped_history(ad, car):
            car.add_last_checked_toped_link(ad.link)
            # TODO: unite adding and commiting to one function somehow
            self.db.commit()
            return
        if self._should_be_added_to_history(ad, car):
            car.add_last_checked_link(ad.link)
            # TODO: unite adding and commiting to one function somehow
            self.db.commit()
            return
    
    async def _process_row_in_queue(self, row: AdQueue):
        queue = row.queue
        car = self.db.query(CarModel).filter(CarModel.id == row.car_model_id).first()
        searches = self.db.query(CarSearch).filter(CarSearch.car_model_id == row.car_model_id)
        ads = list(map(lambda el: AutoAdvertisementPage(el), queue))
        await asyncio.gather(*[ad.get_page_text() for ad in ads])
        for ad in ads:
            res = self.ollama.process(ad_text=ad.text, car=car)
            if res['is_valid_ad']:
                res['price'] = ad.price
                for search in searches:
                    if self._fits_to_search_criteria(res, search, car):
                        self._send_new_ad_notification(search, ad, car)
            await self._add_checked_ad_to_history(ad, car)
            queue.remove(ad.link)
            row.queue = queue
            self.db.commit()


    async def process_queue(self):
        queue_rows = (
            self.db.query(AdQueue)
            .filter(AdQueue.queue.isnot(None))
            .all()
        )
        for row in queue_rows:
            await self._process_row_in_queue(row)

