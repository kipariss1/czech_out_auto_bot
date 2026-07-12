from src.settings.settings import settings
from src.database_utils.interfaces.database_handler import DatabaseHandler
from src.database_utils.sqlite_database import SqliteDBHandler
from src.database_utils.postgres_database import PostgresDBHandler
from src.models.models import Base


class DBFactory:
    
    @staticmethod
    def create_db_handler() -> DatabaseHandler:
        if settings.is_postgres_env:
            return PostgresDBHandler(Base)
        if settings.env == 'test':
            return SqliteDBHandler(Base)

        raise ValueError(f"Unsupported ENV value for database handler: {settings.env}")
