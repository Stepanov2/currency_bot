
CURRENCY_SYNONYMS={
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
    import re
    while True:
        what = input()
        for synonym in CURRENCY_SYNONYMS.keys():
            what = re.sub(synonym,
                          CURRENCY_SYNONYMS[synonym],
                          what,
                          flags=re.IGNORECASE)
        print(what)