import pytest
from src.database.sqlite_database import SqliteDBHandler
import src


@pytest.fixture(scope="session")
def test_db(monkeypatch):
    test_db_handler = SqliteDBHandler("test.db")
    monkeypatch.setitem(src, "sqlite_db_handler", test_db_handler)
    yield test_db_handler.get_db_connection()
    test_db_handler.close_db_connection()
    del test_db_handler
