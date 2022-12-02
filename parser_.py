"""This file defines classes for parser operators, operands, cases and the parser itself.
Import all of the above into your project to create your own parser.
"""

from dataclasses import dataclass, field
import re
from typing import Union


class ParsingFailure(Exception):
    """Raised if unable to parse."""
    pass


def combinations(iterable) -> tuple:
    """This splits list into two in every possible way."""
    length = len(iterable)
    if length < 2:
        raise ValueError("Can't split an iterable with length of 1")
    for i in range(1, length):
        yield iterable[0:i], iterable[i:length]
    return


def protect_from_value_errors(func):
    """Helper decorator."""  # todo: maybe add more types of exceptions
    def wrapper(*args):
        try:
            return func(*args)
        except ValueError as e:
            return f"Ощибочка вышла:\n{e}"
        except OverflowError as e:
            return f"Слищком многа:\n{e}"
    return wrapper


@dataclass(frozen=True, init=True)
class ParserOperator:
    """Give a string that is to be interpreted as an operator, give list of strings to give operator some aliases.
    Example: plus_operator = ParserOperator('+', ['plus', 'add']
    """
    operator: str = field(init=True)
    aliases: list = field(default_factory=list, init=True)

    def check(self, input:str) -> bool:
        """Checks if input string is an operator"""
        if input.lower().strip() == self.operator or input.lower().strip() in self.aliases:
            return True
        return False

    def __str__(self):
        return self.operator


class ParserOperand:
    """Specify limitations imposed on particular type of operand.
    Operand type may be list, string, float or int.
    Note: string and int are not implemented at the moment.
    For list, you must specify a list of compatible strings.
    You can optionally provide a dictionary of synonyms for list type operand.
    Any string matching a key in this dictionary will be replaced with the value of said key.
    You can optionaly provide an additional check on the operand via operand_checker.
    For example operand_checker=lambda x: x > 0 will match only positive numbers.
    """
    def __init__(self, operand_type: str,
                 operand_checker: Union[callable, None] = None,
                 operand_list: Union[list, None] = None,
                 synonym_dict: Union[dict, None] = None):

        possible_operand_types = ('list', 'string', 'float', 'int')
        if operand_type not in possible_operand_types:
            raise ValueError("Incorrect operand type. Try 'list', 'string' 'float' or 'int'")
        if operand_type in ('string', 'int'):
            raise NotImplementedError('Maybe next time')
        if operand_type == 'list' and not isinstance(operand_list, list):
            raise ValueError('Must specify a list of possible values, if operand_type == "list"')

        if operand_type == 'float':
            self.check = self._check_float
            self._operand_type = 'float'
        elif operand_type == 'list':
            self.check = self._check_list
            self._operand_type = 'list'
        self._operand_type = operand_type

        if operand_checker is not None:
            self._operand_checker = operand_checker
        else:
            self._operand_checker = lambda x: True  # All hail Hindi Code!

        if operand_list is not None:
            self.operand_list = operand_list

        if synonym_dict is not None:
            self.synonym_dict = synonym_dict
        else:
            self.synonym_dict = None

    def __str__(self):
        return self.operand_type

    @property
    def operand_type(self):
        return self._operand_type

    def _check_float(self, what: str) -> Union[float, None]:
        """Returns float if it is possible to interpret argument 'what' as such, None otherwise"""

        what = re.sub('[ ]', '', what)  # turns 250 000 into 250000

        try:  # to simply convert into float
            value = float(what)
            if self._operand_checker(value):
                return value
        except ValueError:
            pass

        try:  # to turn 1,23 into 1.23
            value = float(re.sub('[,]', '.', what, 1))

            # Making sure we didn't turn 125,000 into 125.0
            # todo it works great for currencies, but not for numbers in general
            if len(re.split('[,]', what)[-1]) > 2:
                raise ValueError
            if self._operand_checker(value):
                return value
        except ValueError:
            pass

        try:  # to turn 10'000 or 10,000 into 10000
            value = float(re.sub("[,']", '', what))
            if self._operand_checker(value): return value
        except ValueError:
            pass

        try:  # to do both
            value = float(re.sub('[,]', '.', re.sub("[,']", '', what), 1))
            if self._operand_checker(value): return value
        except ValueError:
            pass

        # If all of the above failed, string can not be converted to float
        return None

    def _check_list(self, what: str) -> Union[str, None]:
        """Returns str of operand in correct case if argument 'what' can be interpreted as such, None otherwise"""
        what = what.strip()

        if self.synonym_dict is not None:  # substituting synonyms
            for synonym in self.synonym_dict.keys():
                what = re.sub(synonym,
                              self.synonym_dict[synonym],
                              what,
                              flags=re.IGNORECASE)

        for each in self.operand_list:  # searching for what in list of possible values for this operand.
            if each.lower() == what.lower():
                return each

        # If all of the above failed:
        return None


# some general purpose operands are specified here:
genericFloatOperand = ParserOperand('float')
genericFloatNotZeroOperand = ParserOperand('float', operand_checker=lambda x: x != 0)
genericFloatPositiveOperand = ParserOperand('float', operand_checker=lambda x: x > 0)
genericFloatNotNegativeOperand = ParserOperand('float', operand_checker=lambda x: x >= 0)


class ParserCase:
    """To create a parser case, feed it ParserOperands and ParserOperators in order in which they appear in expression.
    Note:This currently doesn't support unary operators. Only binary ones with one or two operand either side of it.
    To make ParserCase actually do something there are two options:
    To specify simple behaviour use optional quick_action argument.
    Quick action will be protected from errors via "protect_from_value_errors" decorator.
    To specify more complex behaviour create a child of this class and overload _action method.
    _action must return something that has a __str__ method.
    You can use each Parser case as a standalone Parser (via "parse" method). Or feed multiple parser cases to a
    Parser class instance and check for all of them via Parser's "parse" method.
    """

    def __init__(self, *args: Union[ParserOperand, ParserOperator],
                 quick_action: Union[callable, None] = None):

        self._operator = None
        self.left_side_operands = []
        self.right_side_operands = []

        for arg in args:  # Todo additional type checking needed?
            if isinstance(arg, ParserOperator):
                if self._operator is None:
                    self._operator = arg
                    continue
                else:
                    raise TypeError("Can't have more than one opeator per case.")

            if isinstance(arg, ParserOperand):
                if self._operator is None:  # populating left side operators
                    if len(self.left_side_operands) == 2:
                        raise TypeError("Can't have more than two operands either side of operator (for now)")
                    else:
                        self.left_side_operands.append(arg)

                else:  # populating right side operators
                    if len(self.right_side_operands) == 2:
                        raise TypeError("Can't have more than two operands either side of operator (for now)")
                    else:
                        self.right_side_operands.append(arg)

        if not len(self.left_side_operands) or not len(self.right_side_operands):
            raise TypeError("Must specify at least one operand either side of operator.")  # todo unary operators

        if quick_action:  # overload _action with quick_action and protect it from errors
            self._action = protect_from_value_errors(quick_action)

    @property
    def get_operator(self):
        return str(self._operator)

    @property
    def get_operator_aliases(self):
        return self._operator.aliases

    def _action(self, *args) -> Union[str, None]:
        """When making a case, create a child of ParserCase and overload _action method with useful code.
        Or specify a lambda via quick_action argument of __init__
        This method will be called by parse with correct arguments in order specified when creating the instance.
        """

        return str(args)

    def parse(self, inputstring: str) -> str:
        """Calls _action with correct operands in the correct order if able to make sense of inputstring,
        Raises ParsingFailure otherwise.
        """

        inputstring = inputstring.strip()

        # Turn "2+3" into "2 + 3" todo Better approach needed
        inputstring = inputstring.replace(self.get_operator, " " + self.get_operator + " ", 1)  # Meh!

        inputwords = inputstring.split()

        # searching for index of operator
        for index, word in enumerate(inputwords):
            if self._operator.check(word):
                break
        else:  #(nobreak)
            raise ParsingFailure('No operator found in string')

        # splitting inputwords into 2 sublists containig everything to the left of the operator
        # and everything to the right of the operator
        leftwords = inputwords[0:index]
        rightwords = inputwords[index+1:len(inputwords)]
        if rightwords == [] or leftwords == []:
            raise ParsingFailure("Not enough operands.")  # todo unary operators

        # ====== Checking left and right operands =======
        # ====== If either fails, check_operands will raise ParsingFailure
        result = self.check_operands(leftwords, self.left_side_operands)
        result.append(*self.check_operands(rightwords, self.right_side_operands))

        # === If parsing was successful - execute action
        return self._action(*result)

    def check_operands(self, words: list, operands: list) -> list:  # todo will something break if @staticmethod ?
        """Gets list of (1 or more) words and list of (1 or 2) operands.
        If it is possible to combine words in such a way that all operand conditions are met, this returns
        a list of valid values to be fed into _action.
        Raises ParsingFailure otherwise.
        """

        if len(operands) > len(words):
            raise ParsingFailure('Not enough operands')

        if len(operands) == 1:  # 1 operand
            result = operands[0].check(' '.join(words))
            if result is None:
                raise ParsingFailure('No valid operands')
            else:
                return [result]

        else:  # 2 operands
            for possible_options in combinations(words):
                result1 = operands[0].check(' '.join(possible_options[0]))
                result2 = operands[1].check(' '.join(possible_options[1]))
                if result1 is not None and result2 is not None:
                    break
            else:  # (nobreak)
                raise ParsingFailure('No valid operands')
            return [result1, result2]


class Parser:
    """Feed multiple ParserCase instances into this Class to be able to check each of them via parse method. """
    def __init__(self, *parsers: ParserCase):
        self.parsers=[]
        for parser in parsers:
            self.parsers.append(parser)

    @property
    def parser_count(self):
        return len(self.parsers)

    def parse(self, string):
        """Try every parser."""
        for parser in self.parsers:
            try:
                return parser.parse(string)
            except ParsingFailure:
                continue
        return f"Can't parse '{string}'"


if __name__ == '__main__':
    print(__doc__)
