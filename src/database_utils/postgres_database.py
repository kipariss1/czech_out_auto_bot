from src.database_utils.interfaces.database_handler import DatabaseHandler
from src.settings.settings import settings


POSTGRES_PORT = 5432
LOCAL_POSTGRES_HOST = "localhost"
PRODUCTION_POSTGRES_HOST = "postgres_db"


class PostgresDBHandler(DatabaseHandler):

    @staticmethod
    def _db_url_for_host(host: str) -> str:
        postgres_data = settings.postgres_data
        return (
            f"postgresql://{postgres_data['user']}:{postgres_data['password']}"
            f"@{host}:{POSTGRES_PORT}/{postgres_data['db']}"
        )

    @staticmethod
    def db_url() -> str:
        if settings.env == "local":
            return PostgresDBHandler._db_url_for_host(LOCAL_POSTGRES_HOST)
        if settings.env == "production":
            return PostgresDBHandler._db_url_for_host(PRODUCTION_POSTGRES_HOST)

        raise ValueError(f"Unsupported ENV value for Postgres database URL: {settings.env}")
