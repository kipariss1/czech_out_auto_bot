import pytest
from tests.test_saving_language.mock_bot import MockBot
from unittest.mock import MagicMock
import run_bot


@pytest.fixture
def mock_bot(monkeypatch) -> MockBot:
    mb = MockBot()
    monkeypatch.setattr(run_bot, "bot", mb)
    yield mb


@pytest.fixture
def user_id():
    return 3125


@pytest.fixture
def start_message(user_id):
    message = MagicMock()
    message.text = "/start"
    message.from_user.id = user_id
    return message


@pytest.fixture
def ru_lang_message(user_id):
    message = MagicMock()
    message.text = "/ru"
    message.from_user.id = user_id
    return message


def test_language_saved_to_db(mock_bot, start_message, ru_lang_message, user_id):
    mock_bot.add_handler(run_bot.start, {"message": start_message})
    mock_bot.add_handler(run_bot.set_users_language, {"message": ru_lang_message})
    mock_bot.infinity_polling()
    user = run_bot.get_or_create_user(user_id)
    assert user.language == "ru"
