import unittest
from parser_ import *


class ParserOperatorTest(unittest.TestCase):

    def setUp(self):
        self.operator1 = ParserOperator('hell')
        self.operator2 = ParserOperator('yeah', ['baby', '!'])

    def test_parser_operator(self):
        self.assertEqual(str(self.operator1), 'hell')
        self.assertEqual(str(self.operator2), 'yeah')
        for val in ('yeah', 'baby', '!'):
            self.assertEqual(self.operator2.check(val), True)


class ParserOperandTest(unittest.TestCase):

    def setUp(self):
        self.operand1 = ParserOperand('float', operand_checker=lambda x: x >= 0)
        self.operand3 = ParserOperand('float')
        self.operand2 = ParserOperand('list', operand_list=['foo', 'bar', 'PY', 'Thon'])

    def test_float(self):
        valid_inputs = {"100": 100.0,
                  "12.5": 12.5,
                  "120 000": 120000.0,
                  "120'000": 120000.0,
                  "120,000": 120000.0,
                  "12,45": 12.45,
                  "12,4": 12.4,
                  "12,": 12.0,
                  "1.25e6": 1_250_000 }
        print("Valid inputs:")
        for input, output in valid_inputs.items():
            print(input, output)
            self.assertAlmostEqual(self.operand1.check(input), output)
            self.assertAlmostEqual(self.operand3.check(input), output)
        invalid_inputs = ("in", "в", "pink googles", "1.25 USD", "-42")
        print('Invalid inputs:')
        for input in invalid_inputs:
            print(input)
            self.assertIsNone(self.operand1.check(input))

    def test_list(self):
        valid_inputs = ['foo', 'bar', 'PY', 'Thon']
        for each in valid_inputs:
            self.assertEqual(self.operand2.check(each), each)
            self.assertEqual(self.operand2.check(each.upper()), each)
            self.assertEqual(self.operand2.check(each.lower()), each)
        pass

    def test_list_with_synonyms(self):  # todo synonyms
        pass


class CombinationsTest(unittest.TestCase):
    def test_combinations(self):

        testlist = [1]
        test=combinations(testlist)
        with self.assertRaises(ValueError):
            value=next(test)

        testlist = [1, 2, 3, 4]
        test = combinations(testlist)
        value = next(test)
        self.assertEqual(([1], [2, 3, 4]), value)
        value = next(test)
        self.assertEqual(([1, 2], [3, 4]), value)
        value = next(test)
        self.assertEqual(([1, 2, 3], [4]), value)
        #print (next(test))
        with self.assertRaises(StopIteration):
            next(test)


class ParserCaseTest(unittest.TestCase):

    def setUp(self):
        #ParsingFailure
        currencyOperator = ParserOperator('in', aliases=['в', ])
        currencyValueOperand = ParserOperand('float', operand_checker=lambda x: x > 0)
        currencyCodeOperand = ParserOperand('list', operand_list=['USD', 'EUR', 'GBP', 'RUB'])

        self.currencyConversionParser = ParserCase(currencyValueOperand,
                                              currencyCodeOperand,
                                              currencyOperator,
                                              currencyCodeOperand)
        # print(currencyConversionParser.left_side_operands[0],
        #       currencyConversionParser.right_side_operands,
        #       currencyConversionParser.get_operator,
        #       currencyConversionParser.get_operator_aliases, sep='\n')

    def test_currency_parser(self):
        values = ('250000 USD в RUB',
                  '250 000 USD в RUB',
                  '27,56 RUB в GBP',
                  ' 250 000  USD   в   RUB ',)
        try:
            for value in values:

                _ = self.currencyConversionParser.parse(value)
        except ParsingFailure as e:
            print(value)


if __name__ == '__main__':
    unittest.main()
