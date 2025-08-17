from src.database_utils.interfaces.database_handler import DatabaseHandler
from src.settings.settings import settings
import sqlalchemy as sa

class PostgresDBHandler(DatabaseHandler):

    @staticmethod
    def _db_url():
        return f"postgresql://{settings.postgres_data['user']}:{settings.postgres_data['password']}@postgres_db:5432/{settings.postgres_data['db']}"

    def init_engine(self):
        return sa.create_engine(self._db_url())
    
    # TODO: make it automatically upload cars