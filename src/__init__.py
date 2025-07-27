from src.database_utils.sqlite_database import SqliteDBHandler
from src.settings.security.cipher_handler import CipherHandler
from pathlib import Path

SRC_DIR = Path(__file__).parent
sqlite_db_handler = SqliteDBHandler()
cipher_handler = CipherHandler()
