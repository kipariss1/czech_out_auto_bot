from src import bot
from telebot import types

@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("👋 Поздороваться")
    markup.add(btn1)
    bot.send_message(message.from_user.id, "👋 Привет! Я твой бот-huyeplet!", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def get_text_messages(message):
    bot.reply_to(message, "Zdarova zajebal")

bot.infinity_polling()
