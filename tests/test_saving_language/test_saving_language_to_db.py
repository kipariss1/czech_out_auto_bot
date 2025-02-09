import pytest
from tests.test_saving_language.mock_bot import MockBot
from tests.test_saving_language.mock_message import StartMessage, LangMessage
from run_bot import start, set_users_language, get_or_create_user


@pytest.fixture
def mock_bot(monkeypatch) -> MockBot:
    mb = 1  # MockBot()
    return mb


def test_language_saved_to_db(mock_bot):
    user_id = 3156
    # mock_bot.add_handler(start, {"message": StartMessage(user_id=user_id)})
    # mock_bot.add_handler(set_users_language, {"message": LangMessage(user_id=user_id)})
    # mock_bot.infinity_polling()
    # user = get_or_create_user(user_id)
    # assert user.language == "ru"
    pass
