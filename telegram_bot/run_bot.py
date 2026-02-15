from src.settings.security import cipher_handler
from telegram_bot import bot
from telebot import types
from telebot.types import WebAppInfo
from src.models.models import User
from src.settings.settings import settings
from src.database_utils import db_handler


def get_or_create_user(user_id):
    db = db_handler.get_db_connection()
    user = db.query(User).filter_by(id=user_id).first()
    if user is None:
        user = User(id=user_id)
        db.add(user)
        db.commit()
    return user


@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    get_or_create_user(user_id)
    markup = types.InlineKeyboardMarkup()
    open_btn_text = "Open Web app"
    reply_message = (
        "Hello,\n this bot can help you to track the advertisements of specific model of a car with specific parameters on bazos.cz",
    )
    markup.add(
        types.InlineKeyboardButton(
            web_app=WebAppInfo(
                url=f"{settings.base_url}/?enc_user_id={cipher_handler.url_safe_encode(str(message.from_user.id))}"
            ),
            text=open_btn_text,
        )
    )
    bot.reply_to(message, reply_message, reply_markup=markup)


if __name__ == "__main__":
    bot.infinity_polling()
