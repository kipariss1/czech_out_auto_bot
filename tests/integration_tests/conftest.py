import os

from tests.pytest_fixtures.common import build_mock_db, build_mock_bazos


os.environ.setdefault("BOT_TOKEN", "test-token")

try:
    import telebot.util

    telebot.util.validate_token = lambda token: True
except ModuleNotFoundError:
    pass
