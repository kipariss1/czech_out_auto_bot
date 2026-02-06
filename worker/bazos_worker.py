from src.database_utils import db_handler

class BazosWorker:
    
    def __init__(self):
        self.db = db_handler.get_db_connection()

    def process_queue(self):
        pass