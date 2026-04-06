import os
from unittest.mock import Mock

from tests.pytest_fixtures.common import build_mock_db, build_mock_bazos


os.environ.setdefault("BOT_TOKEN", "test-token")

try:
    import telebot

    telebot.TeleBot = Mock(return_value=Mock())
except ModuleNotFoundError:
    pass
