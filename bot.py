"""Run this file to launch the bot!
Make sure to paste your API key into config_bot_sample.py and to rename it to config_bot.py first!
"""

from config_bot import TOKEN
import telebot
from bot_parser import CurrencyConverter, telegramParser
import time

if __name__ == "__main__":

    # initializing bot
    bot = telebot.TeleBot(TOKEN)

    # ========== bot.handlers ===============
    @bot.message_handler(commands=['start', 'help'])
    def say_hello(message: telebot.types.Message):
        bot.reply_to(message, f'Привет, {message.from_user.full_name}!\n'
                              f'Этот бот позволяет конвертировать курсы валют.\n'
                              f'Например, введи "120 USD in GBP" или  "EUR 100 в CHF".\n'
                              f'Писать большими буквами - не обязательно. "100 eur" - тоже работает.\n'
                              f'Напиши /values, чтобы получить список всех доступных валют'
                              f'Для популярных валют предусмотрены псевдонимы.\n'
                              f'Например можно написать "1000 баксов в рублях".\n'
                              f'Можно писать 100\'000 или 100 000, или 100,000.\n'
                              f'Только не забывай про пробелы.\n'
                              f'"100 USD in CHF" - работает. "100USD in CHF" - не работает.\n'
                              f'Ещё можно пользоваться этим ботом как простым калькулятором.\n'
                              f'Например, "150 * 20", "2 ^ 4".\n'
                              f'Нет, много операций на строчку - нельзя.\n'
                              f'Нет, "27 + 45 USD in EUR" - нельзя.\n'
                              f'У автора погорел дедлайн и он не успел)\n'
                              f'<3\n'
                              f'P.S. Напиши /start или /help, чтобы вывести это сообщение ещё раз.')

    @bot.message_handler(commands=['values'])
    def list_currencies(message: telebot.types.Message):
        bot.reply_to(message, f'{CurrencyConverter.return_list_of_currencies()}')


    @bot.message_handler(content_types=['text'])
    def parse_command(message: telebot.types.Message):
        bot.reply_to(message, telegramParser.parse(message.text))


    @bot.message_handler(content_types=['sticker'])
    def praise_sticker(message: telebot.types.Message):
        bot.reply_to(message, 'Отличный стикер, Бро!')

    while True:
        # Activating bot
        try:  # hopefully this will help with disconnects
            bot.polling(non_stop=True)
        except Exception:  # This is bad practice, but it's kinda hard to test what might be Raised here :-/
            time.sleep(5)
            continue