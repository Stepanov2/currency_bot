import telebot
from config_bot import *
from parser_ import *
from synonyms import CURRENCY_SYNONYMS
import requests
import json
import time
# import logging  # todo

# Since this can be used for other ParserCases. this is initialized outside CurrencyConverter
in_operator = ParserOperator('in', aliases=['в'])


class CurrencyConverter(ParserCase):
    """This extends ParserCase with logic necessary for currency conversion"""
    API_URL = 'https://cdn.cur.su/api/latest.json'
    MAX_RETRIES = 5
    TIMEOUT_BETWEEN_ATTEMPTS = 1  # second
    RATES_BECOME_OBSOLETE_AFTER = 180  # seconds
    rates = {}
    _rates_last_checked = None
    _rates_obsolete = False

    def __init__(self, reverse: bool = False):
        CurrencyConverter.update_currency_rates()  # todo this happens twice, since I init two instances (norm and rev)

        # initializing operands
        currency_value_operand = genericFloatPositiveOperand
        currency_code_operand = ParserOperand('list',
                                              operand_list=list(CurrencyConverter.rates.keys()),
                                              synonym_dict=CURRENCY_SYNONYMS)

        # calling ParserCase init with normal or reversed operand order
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

        # Try to contact the API_URL MAX_RETRIES times
        for tries in range(cls.MAX_RETRIES):
            print(f'Attempt #{tries+1} to reach API.')
            try:  # didn't now this will raise an exception
                answer = requests.get(cls.API_URL, timeout=3)
            except requests.exceptions.ReadTimeout:
                time.sleep(cls.TIMEOUT_BETWEEN_ATTEMPTS)
                continue
            except requests.exceptions.ConnectionError:
                time.sleep(cls.TIMEOUT_BETWEEN_ATTEMPTS)
                continue
            if answer.status_code != 200:
                time.sleep(cls.TIMEOUT_BETWEEN_ATTEMPTS)
            else:
                break
        else:  # (nobreak) failed to get rates...
            if cls._rates_last_checked is not None:  # ...during runtime:
                cls._rates_obsolete = True  # This will add a warning to answer
                cls._rates_last_checked = time.time()  # this makes sure rates won't be updated again for some time
                print('FYI, API is down.')
                return
            else:  # ...during __init__. No point in going further then.
                print('Was unable to get currency rates! What a shame!')
                quit(1)

        # On Success:
        cls.rates = json.loads(answer.content)['rates']
        cls._rates_obsolete = False
        cls._rates_last_checked = time.time()
        print("Sucsessfully fetched rates from API")

    @classmethod
    def return_list_of_currencies(cls):
        """If ISO_4217 dictionary exists, try to fetch human-readable currency names from it."""

        answer = ''
        # todo: list aliases first
        for currency_code in sorted(cls.rates.keys()):
            answer += currency_code
            try:
                answer += f' ({ISO_4217[currency_code]})'
            except KeyError:  # todo more types of error?
                pass
            except ReferenceError:
                pass
            answer += '\n'

        return answer

    def _action(self, value, orig_currency, target_currency):
        """Overrides parent's _action method."""

        # check if we need to update exchange rates
        if time.time() - CurrencyConverter._rates_last_checked > CurrencyConverter.RATES_BECOME_OBSOLETE_AFTER:
            CurrencyConverter.update_currency_rates()

        # checking "polarity"=)
        if self.reversed:
            orig_currency, value = value, orig_currency

        # figuring exchange rate for given currency pair
        if orig_currency == 'USD':
            answer = value * CurrencyConverter.rates[target_currency]
        elif target_currency == 'USD':
            answer = value / CurrencyConverter.rates[orig_currency]
        else:
            answer = value * (CurrencyConverter.rates[target_currency] /
                              CurrencyConverter.rates[orig_currency])

        # this will be returned to user
        string_to_return = f"{str(round(value, 2))} {orig_currency} = {str(round(answer, 2))} {target_currency}"

        # + make sure to shame user if he asks for silly things =)
        if orig_currency == target_currency:
            string_to_return += '\n🤔🤔🤔🤔🤔🤔🤔🤔🤔🤔'

        # + make sure to inform user that rates are obsolete
        if CurrencyConverter._rates_obsolete:
            string_to_return += '\n Please note that the rates are not up to date due to remote server problem.'

        return string_to_return


if __name__ == "__main__":

    # Initializing Currency conversion parser cases
    currencyConverterNormal = CurrencyConverter()
    currencyConverterReversed = CurrencyConverter(reverse=True)

    # Making some operators for arithmetic operations
    add_operator = ParserOperator('+')
    subtract_operator = ParserOperator('-')
    multiply_operator = ParserOperator('*')
    divide_operator = ParserOperator('/')
    power_operator = ParserOperator('^', aliases=['**'])  # hello, python =)
    sqrt_operator = ParserOperator('sqrt', aliases=['root'])  # todo unary operators

    # And creating parser cases for said operations
    generic_parsers = list()
    generic_parsers.append(ParserCase(genericFloatOperand,  # addition
                                      add_operator,
                                      genericFloatOperand,
                                      quick_action=lambda a, b: str(a+b)))

    generic_parsers.append(ParserCase(genericFloatOperand,  # subtraction
                                      subtract_operator,
                                      genericFloatOperand,
                                      quick_action=lambda a, b: str(a-b)))

    generic_parsers.append(ParserCase(genericFloatOperand,  # multiplication
                                      multiply_operator,
                                      genericFloatOperand,
                                      quick_action=lambda a, b: str(a*b)))

    generic_parsers.append(ParserCase(genericFloatOperand,  # division
                                      divide_operator,
                                      genericFloatNotZeroOperand,
                                      quick_action=lambda a, b: str(a/b)))

    generic_parsers.append(ParserCase(genericFloatPositiveOperand,  # power
                                      power_operator,
                                      genericFloatOperand,
                                      quick_action=lambda a, b: str(a**b)))

    # todo: single operand operators =)
    # generic_parsers.append(ParserCase(sqrt_operator,
    #                                   genericFloatNotNegativeOperand,
    #                                   quick_action=lambda a: str(a ** 0.5)))

    # ======================================================
    # feeding all the parser cases created above into parser
    telegramParser=Parser(currencyConverterNormal, currencyConverterReversed, *generic_parsers)

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
        try:  # hopefylly this will help with disconnects
            bot.polling(non_stop=True)
        except Exception:  # This is bad practice, but it's kinda hard to test what might be Raised here :-/
            time.sleep(5)
            continue