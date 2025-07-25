import telebot
from src.database_utils.sqlite_database import SqliteDBHandler
from src.settings.security.cipher_handler import CipherHandler
import os

token = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(token)
sqlite_db_handler = SqliteDBHandler()
cipher_handler = CipherHandler()
