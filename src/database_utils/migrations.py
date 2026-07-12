from pathlib import Path

from alembic.config import Config

from src.database_utils.postgres_database import PostgresDBHandler
from src.database_utils.sqlite_database import SqliteDBHandler
from src.settings.settings import settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = PROJECT_ROOT / "alembic.ini"
ALEMBIC_VERSIONS_PATH = PROJECT_ROOT / "alembic" / "versions"


def has_migrations() -> bool:
    return ALEMBIC_VERSIONS_PATH.exists() and any(
        path.is_file() and not path.name.startswith("__")
        for path in ALEMBIC_VERSIONS_PATH.glob("*.py")
    )


def get_database_url() -> str:
    if settings.is_postgres_env:
        return PostgresDBHandler.db_url()
    if settings.env == "test":
        return SqliteDBHandler.db_url()

    raise ValueError(f"Unsupported ENV value for database migrations: {settings.env}")


def get_alembic_config() -> Config:
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("sqlalchemy.url", get_database_url())
    return alembic_cfg
