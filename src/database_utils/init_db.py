from pathlib import Path

from alembic import command
from alembic.config import Config

from src.database_utils import db_handler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = PROJECT_ROOT / "alembic.ini"
ALEMBIC_VERSIONS_PATH = PROJECT_ROOT / "alembic" / "versions"


def has_migrations() -> bool:
    return any(
        path.is_file() and not path.name.startswith("__")
        for path in ALEMBIC_VERSIONS_PATH.glob("*.py")
    )


def run_migrations() -> None:
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))
    command.upgrade(alembic_cfg, "head")


def init_db() -> None:
    if has_migrations():
        run_migrations()
    else:
        db_handler.create_tables()

    db_handler.updload_cars_to_db()


if __name__ == "__main__":
    init_db()
