from src.database_utils import db_handler
from src.models.models import AdQueue, CarModel, CarSearch
from queue_svc.bazos_api.auto_bazos_api import AutoAdvertisementPage
from queue_svc.ollama_api.ollama_client import OllamaClient
import asyncio

class BazosWorker:
    
    def __init__(self):
        self.db = db_handler.get_db_connection()
        self.ollama = OllamaClient()

    async def process_queue(self):
        queue_rows = (
            self.db.query(AdQueue)
            .filter(AdQueue.queue.isnot(None))
            .all()
        )
        for row in queue_rows:
            queue = row.queue
            car = self.db.query(CarModel).filter(CarModel.id == row.car_model_id)
            searches = self.db.query(CarSearch).filter(CarSearch.car_model_id == row.car_model_id)
            ads = list(map(lambda el: AutoAdvertisementPage(el), queue))
            await asyncio.gather(*[ad.get_page_text() for ad in ads])
            for ad in ads:
                res = self.ollama.process(ad_text=ad.text, car=car)
                # TODO: here make comparison of every search and parsed app !BUT! it requires change of model CarSearch (TBD)


            

