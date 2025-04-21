import telebot
from src.database.sqlite_database import SqliteDBHandler
from src.settings.security.cipher_handler import CipherHandler
from src.settings.settings import Settings
import os

token = os.getenv("czech_out_auto_bot_token")
bot = telebot.TeleBot(token)
sqlite_db_handler = SqliteDBHandler()
cipher_handler = CipherHandler()
