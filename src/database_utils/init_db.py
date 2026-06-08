from alembic import command

from src.database_utils import db_handler
from src.database_utils.migrations import get_alembic_config, has_migrations


def run_migrations() -> None:
    command.upgrade(get_alembic_config(), "head")


def init_db() -> None:
    if has_migrations():
        run_migrations()
    else:
        db_handler.create_tables()

    db_handler.updload_cars_to_db()


if __name__ == "__main__":
    init_db()
