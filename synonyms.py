"""This file contains synonyms for currencies.
Each dict key is a regex that will be replaced by corresponding value.
"""

CURRENCY_SYNONYMS = {
    'доллар[\\w]*': 'USD',
    'долар[\\w]*': 'USD',
    'бакс[\\w]*': 'USD',
    'бач[\\w]*': 'USD',
    'dollar[\\w]*': 'USD',
    'рубл[\\w]*': 'RUB',
    'деревян[\\w]*': 'RUB',
    'rouble[\\w]*': 'RUB',
    'фунт[\\w]*': 'GBP',
    'pound[\\w]*': 'GBP',
    'йен[\\w]*': 'JPY',
    'yen[\\w]*': 'JPY',
    'юан[\\w]*': 'CNY',
    'yan[\\w]*': 'CNY',
    'frank': 'CHF',
    'франк[\\w]*': 'CHF',
    '\$': 'USD',
    '£': 'GBP',
    '€': 'EUR',
    'евро': 'EUR',
    'euro[\\w]*': 'EUR',
    'evro': 'EUR',

}


if __name__ == "__main__":
    """This lets you test your synonyms in console."""
    import re
    while True:
        what = input()
        for synonym in CURRENCY_SYNONYMS.keys():
            what = re.sub(synonym,
                          CURRENCY_SYNONYMS[synonym],
                          what,
                          flags=re.IGNORECASE)
        print(what)
