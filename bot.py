import telebot
from config_bot import *
from parser_ import *
from synonyms import CURRENCY_SYNONYMS
import requests
import json
import time
import logging


in_operator = ParserOperator('in', aliases=['в'])
class CurrencyConverter(ParserCase):
    API_URL = 'https://cdn.cur.su/api/latest.json'
    MAX_RETRIES = 5
    TIMEOUT_BETWEEN_ATTEMPTS = 1  # second
    RATES_BECOME_OBSOLETE_AFTER = 10  # seconds # todo change
    rates = {}
    _rates_last_checked = None
    _rates_obsolete = False

    def __init__(self, reverse: bool = False):
        CurrencyConverter.update_currency_rates()
        currency_value_operand = genericFloatPositiveOperand
        currency_code_operand = ParserOperand('list',
                                              operand_list=list(CurrencyConverter.rates.keys()),
                                              synonym_dict=CURRENCY_SYNONYMS)
        if not reverse:
            super().__init__(currency_value_operand,
                             currency_code_operand,
                             in_operator,
                             currency_code_operand)
            self.reversed = False
        else:
            super().__init__(currency_code_operand,
                             currency_value_operand,
                             in_operator,
                             currency_code_operand)
            self.reversed = True

    @classmethod
    def update_currency_rates(cls):
        """Updates currency rates via api."""
        print('checking_rates')
        for tries in range(cls.MAX_RETRIES):
            answer = requests.get(cls.API_URL, timeout=3)
            if answer.status_code != 200:
                time.sleep(cls.TIMEOUT_BETWEEN_ATTEMPTS)
            else:
                break
        else:  # (nobreak) failed to get rates
            if cls._rates_last_checked is not None:
                cls._rates_obsolete = True
                cls._rates_last_checked = time.time()
                return
            else: # can't fetch rates during __init__
                print('Was unable to get currency rates! What a shame!')
                quit(1)
        print('Обновили курсы')
        cls.rates = json.loads(answer.content)['rates']

        cls._rates_obsolete = False
        cls._rates_last_checked = time.time()

    def _action(self, value, orig_currency, target_currency):

        if time.time() - CurrencyConverter._rates_last_checked > CurrencyConverter.RATES_BECOME_OBSOLETE_AFTER:
            CurrencyConverter.update_currency_rates()

        if self.reversed:
            orig_currency, value = value, orig_currency

        if orig_currency == 'USD':
            answer = value * CurrencyConverter.rates[target_currency]
        elif target_currency == 'USD':
            answer = value / CurrencyConverter.rates[orig_currency]
        else:
            answer = value * (CurrencyConverter.rates[target_currency] /
                              CurrencyConverter.rates[orig_currency])
        string_to_return = f"{str(round(value, 2))} {orig_currency} = {str(round(answer, 2))} {target_currency}"
        if CurrencyConverter._rates_obsolete:
            string_to_return += '\n Please note that the rates are not up to date due to remote server problem.'
        return string_to_return


currencyConverterNormal = CurrencyConverter()
currencyConverterReversed = CurrencyConverter(reverse=True)


# Generic arythmetic parsers
add_operator = ParserOperator('+')
substract_operator = ParserOperator('-')
multiply_operator = ParserOperator('*')
divide_operator = ParserOperator('/')
power_operator = ParserOperator('^', aliases=['**'])  # hello, python
sqrt_operator = ParserOperator('sqrt', aliases=['root'])  # hello, python

generic_parsers=[]
generic_parsers.append(ParserCase(genericFloatOperand,
                                  add_operator,
                                  genericFloatOperand,
                                  quick_action=lambda a, b: str(a+b)))
generic_parsers.append(ParserCase(genericFloatOperand,
                                  substract_operator,
                                  genericFloatOperand,
                                  quick_action=lambda a, b: str(a-b)))
generic_parsers.append(ParserCase(genericFloatOperand,
                                  multiply_operator,
                                  genericFloatOperand,
                                  quick_action=lambda a, b: str(a*b)))
generic_parsers.append(ParserCase(genericFloatOperand,
                                  divide_operator,
                                  genericFloatNotZeroOperand,
                                  quick_action=lambda a, b: str(a/b)))
generic_parsers.append(ParserCase(genericFloatPositiveOperand,
                                  power_operator,
                                  genericFloatOperand,
                                  quick_action=lambda a, b: str(a**b)))
# todo: single operand operators =)
# generic_parsers.append(ParserCase(genericFloatNotNegativeOperand,
#                                   sqrt_operator,
#                                   genericFloatOperand,
#                                   quick_action=lambda a, b: str(a+b)))


telegramParser=Parser(currencyConverterNormal, currencyConverterReversed, *generic_parsers)

# while True:
#     input_ = input()
#     if input_ == '': quit(0)
#     print(telegramParser.parse(input_))




bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'help'])
def say_hello(message: telebot.types.Message):
    bot.reply_to(message, f'Привет, {message.from_user.full_name}!\n'
                          f'Этот бот позволяет конвертировать курсы валют.\n'
                          f'Например, введи "120 USD in GBP" или  "EUR 100 в CHF".\n'
                          f'Писать большими буквами - не обязательно. "100 eur" - тоже работает.\n'
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
                          f'<3')


@bot.message_handler(content_types=['text'])
def parse_command(message: telebot.types.Message):
    bot.reply_to(message, telegramParser.parse(message.text))



@bot.message_handler(content_types=['sticker'])
def praise_sticker(message: telebot.types.Message):
    bot.reply_to(message, 'Отличный стикер, Бро!')


print('Bot is running!')
bot.polling(non_stop=True)



