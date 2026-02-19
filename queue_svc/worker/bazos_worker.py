from src.database_utils import db_handler
from src.models.models import AdQueue, CarModel, CarSearch, User
from queue_svc.bazos_api.auto_bazos_api import AutoAdvertisementPage
from queue_svc.ollama_api.ollama_client import OllamaClient, ValidCarAd
from telegram_bot import bot
import asyncio

class BazosWorker:
    
    def __init__(self):
        self.db = db_handler.get_db_connection()
        self.ollama = OllamaClient()

    @staticmethod
    def _fits_to_search_criteria(car_parse_res: ValidCarAd, search: CarSearch) -> bool:
        return (
            search.mileage_range_from < int(car_parse_res['mileage']) < search.mileage_range_to and
            search.year_range_from < int(car_parse_res['year']) < search.year_range_to
        )
    
    def _send_new_ad_notification(self, search: CarSearch, ad: AutoAdvertisementPage, car: CarModel):
        attrs = search.to_dict()['attributes']
        message = f"""
🚨🏎️ We found new car advertisement, for: {car.manufacturer} {car.model}
with criteria:
    - Year range:   {attrs['Year range']}
    - Mileage range: {attrs['Mileage range']}
    - Price range:  {attrs['Price range']}

Here is the link: {ad.link}
"""
        user = self.db.query(User).filter(User.id == search.user_id).first()
        bot.send_message(
            chat_id=user.telegram_id,
            text=message
        )

    async def _add_checked_ad_to_history(ad: AutoAdvertisementPage, car: CarModel):
        if await ad.is_toped() and ad.link not in car.last_checked_toped_links:
            car.add_last_checked_toped_link(ad.link)
        if ad.link not in car.last_checked_links:
            car.add_last_checked_link(ad.link)
    
    async def _process_row_in_queue(self, row: AdQueue):
        queue = row.queue
        car = self.db.query(CarModel).filter(CarModel.id == row.car_model_id).first()
        searches = self.db.query(CarSearch).filter(CarSearch.car_model_id == row.car_model_id)
        ads = list(map(lambda el: AutoAdvertisementPage(el), queue))
        await asyncio.gather(*[ad.get_page_text() for ad in ads])
        for ad in ads:
            res = self.ollama.process(ad_text=ad.text, car=car)
            if res['is_valid_ad']:
                for search in searches:
                    if self._fits_to_search_criteria(res, search):
                        self._send_new_ad_notification(search, ad, car)
                        await self._add_checked_ad_to_history(ad, car)


    async def process_queue(self):
        queue_rows = (
            self.db.query(AdQueue)
            .filter(AdQueue.queue.isnot(None))
            .all()
        )
        for row in queue_rows:
            await self._process_row_in_queue(row)
            row.queue = None
            self.db.commit()

