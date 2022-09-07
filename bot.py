import telebot
from config_bot import *

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def say_hello(message: telebot.types.Message):
    bot.reply_to(message, f'Привет, {message.from_user.full_name}! '
                          f'Этот бот позволяет конвертировать курсы валют.'
                          f'Возможно, у него появятся и другие функции.'
                          f'Но это - не точно.'
                          f'Набери \\help, чтобы увидеть список команд.')


@bot.message_handler(commands=['help'])
def say_hello(message: telebot.types.Message):
    bot.reply_to(message, 'TODO')# todo


@bot.message_handler(commands=['hello'])
def say_hi(message: telebot.types.Message):
    bot.reply_to(message, 'Hi=)')


@bot.message_handler(content_types=['sticker'])
def praise_sticker(message: telebot.types.Message):
    bot.reply_to(message, 'Отличный стикер, Бро!')


print('Bot is running!')
bot.polling(non_stop=True)



