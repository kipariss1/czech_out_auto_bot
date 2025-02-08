import pytest
from tests.test_saving_language.mock_bot import MockBot


@pytest.fixture
def mock_bot(monkeypatch) -> MockBot:
    mb = MockBot()
    return mb


def make_message(text):
    return {}


def test_language_saved_to_db(test_db, mock_bot):
    pass
