from src import cipher_handler
from telegram_bot import bot
from telebot import types
from telebot.types import WebAppInfo
from src.models.models import User
from src.settings import settings
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
    construct_generic_answer(message, user)


def construct_generic_answer(message, user):
    markup = types.InlineKeyboardMarkup()
    if user.language == "en":
        open_btn_text = "Open Web app"
        reply_message = (
            "Hello,\n this bot can help you to track the advertisements of specific model of a car with specific parameters on bazos.cz",
        )
    if user.language == "ru":
        open_btn_text = "Открыть веб-приложение"
        reply_message = "Здравствуйте,\n этот бот может помочь вам отслеживать новые объявления конкретной модели автомобиля на bazos.cz"
    if user.language == "cz":
        open_btn_text = "Otevřít webovou aplikaci"
        reply_message = "Dobrý den,\n tento bot vám pomůže sledovat inzeráty konkrétního modelu auta s konkrétními parametry na bazos.cz"
    markup.add(
        types.InlineKeyboardButton(
            web_app=WebAppInfo(
                url=f"{settings.base_url}/?enc_user_id={cipher_handler.url_safe_encode(str(message.from_user.id))}"
            ),
            text=open_btn_text,
        )
    )
    bot.reply_to(message, reply_message, reply_markup=markup)


@bot.message_handler(commands=["web"])
def run_web_app(message):
    user = get_or_create_user(message.chat.id)
    construct_generic_answer(message, user)


if __name__ == "__main__":
    bot.infinity_polling()
