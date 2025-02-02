from src import bot
from telebot import types
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
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.InlineKeyboardButton("🇬🇧", callback_data="lang_en")
    btn2 = types.InlineKeyboardButton("🇷🇺", callback_data="lang_ru")
    btn3 = types.InlineKeyboardButton("🇨🇿", callback_data="lang_cz")
    markup.add(btn1, btn2, btn3)
    bot.send_message(
        message.from_user.id, "Select language please", reply_markup=markup
    )


# TODO: fix the query handler, doesn't work with callback
@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_users_language(call):
    lang = call.data.split("_")[1]
    user_id = call.message.chat.id
    db = sqlite_db_handler.get_db_connection()
    user = get_or_create_user(user_id)
    if user.language != lang:
        user.language = lang
        db.commit()


@bot.message_handler(content_types=["text"])
def get_text_messages(message):
    user = get_or_create_user(message.chat.id)
    if user.language == "en":
        bot.reply_to(message, "Hello zajebal")
    if user.language == "ru":
        bot.reply_to(message, "Zdarova zajebal")
    if user.language == "cz":
        bot.reply_to(message, "Cau zajebal")


bot.infinity_polling()
