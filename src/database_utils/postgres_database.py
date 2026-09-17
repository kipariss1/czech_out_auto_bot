from src.database_utils.interfaces.database_handler import DatabaseHandler
from src.settings.settings import settings


POSTGRES_PORT = 5432
PRODUCTION_POSTGRES_HOST = "postgres_db"
LOCAL_TEST_POSTGRES_HOST = "localhost"
LOCAL_TEST_POSTGRES_PORT = 5433


class PostgresDBHandler(DatabaseHandler):

    @staticmethod
    def _db_url_for_host(host: str, port: int = POSTGRES_PORT) -> str:
        postgres_data = settings.postgres_data
        return (
            f"postgresql://{postgres_data['user']}:{postgres_data['password']}"
            f"@{host}:{port}/{postgres_data['db']}"
        )

    @staticmethod
    def db_url() -> str:
        if settings.env == "production":
            return PostgresDBHandler._db_url_for_host(PRODUCTION_POSTGRES_HOST)
        if settings.env in ("local", "test"):
            return PostgresDBHandler._db_url_for_host(LOCAL_TEST_POSTGRES_HOST, LOCAL_TEST_POSTGRES_PORT)

        raise ValueError(f"Unsupported ENV value for Postgres database URL: {settings.env}")
