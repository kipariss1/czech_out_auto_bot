import telebot
from src.database.sqlite_database import SqliteDBHandler
import os

token = os.getenv("czech_out_auto_bot_token")
bot = telebot.TeleBot(token)
sqlite_db_handler = SqliteDBHandler()
