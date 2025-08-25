from src.database_utils.interfaces.database_handler import DatabaseHandler
from src.settings.settings import settings

class PostgresDBHandler(DatabaseHandler):

    @staticmethod
    def db_url():
        return f"postgresql://{settings.postgres_data['user']}:{settings.postgres_data['password']}@postgres_db:5432/{settings.postgres_data['db']}"