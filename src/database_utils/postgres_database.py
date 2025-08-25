from src.database_utils.interfaces.database_handler import DatabaseHandler
from src.settings.settings import settings
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase

class PostgresDBHandler(DatabaseHandler):

    def __init__(self, Base: DeclarativeBase):
        self._engine = self.init_engine()
        self._db_conn = None
        inspector = inspect(self._engine)
        if not inspector.has_table("Users"):
            Base.metadata.create_all(bind=self._engine)

    @staticmethod
    def db_url():
        return f"postgresql://{settings.postgres_data['user']}:{settings.postgres_data['password']}@postgres_db:5432/{settings.postgres_data['db']}"