import telebot
import os

token = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(token)