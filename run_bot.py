from src import bot
from telebot import types
from telebot.types import WebAppInfo
from src.models.models import User
from src import sqlite_db_handler


def get_or_create_user(user_id):
    db = sqlite_db_handler.get_db_connection()
    user = db.query(User).filter_by(id=user_id).first()
    if user is None:
        user = User(id=user_id)
        db.add(user)
        db.commit()
    return user


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message, "Please select your language: \n\t🇬🇧 /EN \n\t🇷🇺 /RU \n\t🇨🇿 /CZ"
    )


@bot.message_handler(commands=["EN", "RU", "CZ"])
def set_users_language(message):
    lang = message.text.replace("/", "").lower()
    user_id = message.from_user.id
    db = sqlite_db_handler.get_db_connection()
    user = get_or_create_user(user_id)
    if user.language != lang:
        user.language = lang
        db.commit()


@bot.message_handler(content_types=["text"])
def get_text_messages(message):
    user = get_or_create_user(message.chat.id)
    if user.language == "en":
        bot.reply_to(
            message,
            "Hello,\n this bot can help you to track the advertisements of specific model of a car with specific parameters on bazos.cz",
        )
    if user.language == "ru":
        bot.reply_to(message, "Здравствуйте,\n этот бот может помочь вам отслеживать новые обвления конкретной модели автомобиля на bazos.cz")
    if user.language == "cz":
        bot.reply_to(message, "Dobrý den,\n tento bot vám pomůže sledovat inzeráty konkrétního modelu auta s konkrétními parametry na bazos.cz")


if __name__ == "__main__":
    bot.infinity_polling()
