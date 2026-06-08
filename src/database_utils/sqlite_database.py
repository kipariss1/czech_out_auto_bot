from src.database_utils.interfaces.database_handler import DatabaseHandler
from src import SRC_DIR


class SqliteDBHandler(DatabaseHandler):

    @staticmethod
    def db_url():
        return f"sqlite:///{(SRC_DIR / 'db' / 'local.db').as_posix()}"
