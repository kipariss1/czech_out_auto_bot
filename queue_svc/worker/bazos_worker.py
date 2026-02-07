from src.database_utils import db_handler
from src.models.models import AdQueue, CarModel, CarSearch
from queue_svc.bazos_api.auto_bazos_api import AutoAdvertisementPage
from queue_svc.ollama_api.ollama_client import OllamaClient, ValidCarAd
import asyncio

class BazosWorker:
    
    def __init__(self):
        self.db = db_handler.get_db_connection()
        self.ollama = OllamaClient()

    @staticmethod
    def fits_to_search_criteria(search: CarSearch, car_parse_res: ValidCarAd) -> bool:
        return (
            search.milage_range_from < int(car_parse_res['mileage']) < search.milage_range_to and
            search.year_range_from < int(car_parse_res['year']) < search.year_range_to
        )
    
    async def _process_row_in_queue(self, row: AdQueue):
        queue = row.queue
        car = self.db.query(CarModel).filter(CarModel.id == row.car_model_id)
        searches = self.db.query(CarSearch).filter(CarSearch.car_model_id == row.car_model_id)
        ads = list(map(lambda el: AutoAdvertisementPage(el), queue))
        await asyncio.gather(*[ad.get_page_text() for ad in ads])
        for ad in ads:
            res = self.ollama.process(ad_text=ad.text, car=car)
            if res.is_valid_ad:
                for search in searches:
                    if self.fits_to_search_criteria(search, res):
                        # TODO: here send ad to the owner of the search
                        pass
                        # TODO: here write checked adds and toped adds to history

    async def process_queue(self):
        queue_rows = (
            self.db.query(AdQueue)
            .filter(AdQueue.queue.isnot(None))
            .all()
        )
        for row in queue_rows:
            self._process_row_in_queue(row)

