import pytest
from src.database.sqlite_database import SqliteDBHandler
import src


@pytest.fixture(scope="session")
def test_db_handler():
    t_db_handler = 1  # SqliteDBHandler("test.db")
    yield t_db_handler
    # t_db_handler.close_db_connection()
    # del t_db_handler


@pytest.fixture(autouse=True)
def test_db(monkeypatch, test_db_handler):
    monkeypatch.setattr(src, "sqlite_db_handler", test_db_handler)
    return test_db_handler  # test_db_handler.get_db_connection()
