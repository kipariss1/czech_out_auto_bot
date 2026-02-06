from src.database_utils import db_handler
from src.models.models import AdQueue
from parser.bazos_api.auto_bazos_api import AutoAdvertisementPage
import asyncio

class BazosWorker:
    
    def __init__(self):
        self.db = db_handler.get_db_connection()

    async def process_queue(self):
        queue_rows = (
            self.db.query(AdQueue)
            .filter(AdQueue.queue.isnot(None))
            .all()
        )
        for row in queue_rows:
            queue = row.queue
            ads = list(map(lambda el: AutoAdvertisementPage(el), queue))
            await asyncio.gather(*[ad.get_page_text() for ad in ads])
            # TODO: here process text in LLM and then check against all CarSearches with same car_id and send the ad to user

