"""This contains input parser methods
Input parser tries to search for "operator" literal and "operands" literals
and returns function to call and parameters for said function.
"""
import importlib #todo
from operand_list import *
from synonyms import *
from dataclasses import dataclass, field
import re
from typing import Union

class ParsingFailure(Exception):
    """Raised if unable to parse."""
    pass


def combinations(iterable) -> tuple:
    """This splits list in two in every possible way."""
    length = len(iterable)
    if length < 2:
        raise ValueError("Can't split an iterable with lenght of 1")
    for i in range(1, length):
        yield iterable[0:i], iterable[i:length]
    return


def protect_from_value_errors(func):
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
    """Give a string to act as an operator, give list of strings to give operator some aliases."""
    operator: str = field(init=True)
    aliases: list = field(default_factory=list, init=True)

    def check(self, input:str) -> bool:
        """Checks if input string is an operator"""
        if input.lower().strip() in self.aliases or input.lower().strip() == self.operator:
            return True
        return False

    def __str__(self):
        return self.operator


class ParserOperand:

    def __init__(self, operand_type: str,
                 operand_checker: Union[callable, None] = None,
                 operand_list: Union[list, None] = None,
                 synonym_dict: Union[dict,None] = None):
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
        """Returns float if it is possible to interpret string as such, None otherwise"""
        what = re.sub('[ ]', '', what) # turns 250 000 into 250000
        try:  # to simply convert into float
            value = float(what)
            if self._operand_checker(value): return value
        except ValueError:
            pass

        try:  # to turn 1,23 into 1.23
            value = float(re.sub('[,]', '.', what, 1))
            # Making sure we didn't turn 125,000 into 125.0
            if len(re.split('[,]', what)[-1]) > 2:
                raise ValueError
            if self._operand_checker(value): return value
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
        # If all of the above failed:
        return None

    def _check_list(self, what:str) -> Union[str, None]:
        """Returns str of operand in correct case if what can be interpreted as such, None otherwise"""
        what = what.strip()  # todo synonyms
        if self.synonym_dict is not None:
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


genericFloatOperand = ParserOperand('float')
genericFloatNotZeroOperand = ParserOperand('float', operand_checker=lambda x: x != 0)
genericFloatPositiveOperand = ParserOperand('float', operand_checker=lambda x: x > 0)
genericFloatNotNegativeOperand = ParserOperand('float', operand_checker=lambda x: x >= 0)


class ParserOperation:
    def __init__(self):
        pass


class ParserCase:
    def __init__(self, *args:Union[ParserOperand, ParserOperator],
                 quick_action:Union[callable, None] = None):
        self._operator = None
        self.left_side_operands = []
        self.right_side_operands = []
        for arg in args:  # Todo check for wrong types as args
            # try:
            #     print(arg.operand_type)
            # except Exception:
            #     print('Operator')
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
                else: # populating right side operators
                    if len(self.right_side_operands) == 2:
                        raise TypeError("Can't have more than two operands either side of operator (for now)")
                    else:
                        self.right_side_operands.append(arg)
        if not len(self.left_side_operands) or not len(self.right_side_operands):
            raise TypeError("Must specify at least one operand either side of operator.")

        if quick_action:
            # self._action = quick_action
            self._action = protect_from_value_errors(quick_action)
    @property
    def get_operator(self):
        return str(self._operator)

    @property
    def get_operator_aliases(self):
        return self._operator.aliases

    def _action(self, *args) -> Union[str, None]:
        """When making a case, create a child of ParserCase and overload _action method with useful code.
        This method is called with correct arguments in order specified when creating the instance.
        Or specify a lambda via quick_action argument of __init__"""
        # for arg in args:
        #     print(arg)
        return args
        pass

    def parse(self, inputstring: str) -> str:
        """Return reply, as specified by action, or raises ParsingFailure"""
        inputstring = inputstring.strip()
        inputstring = inputstring.replace(self.get_operator, " " + self.get_operator + " ", 1)  # Meh!
                                                                                        # Better approach needed
        inputwords = inputstring.split()
        for index, word in enumerate(inputwords):
            if self._operator.check(word):
                break
        else:  #(nobreak)
            raise ParsingFailure('No operator found in string')
        # print(self.left_side_operands[0].operand_type, self.left_side_operands[1].operand_type)
        # print(self.right_side_operands[0].operand_type)
        leftwords = inputwords[0:index]
        rightwords = inputwords[index+1:len(inputwords)]
        if rightwords == [] or leftwords == []:
            raise ParsingFailure("Not enough operands.")

        # ====== Checking left and right operands =======
        # ====== If either fails, check_operands will raise ParsingFailure

        result = self.check_operands(leftwords, self.left_side_operands)
        result.append(*self.check_operands(rightwords, self.right_side_operands))

        # === If parsing was successful - execute action

        return self._action(*result)



    def check_operands(self, words:list, operands:list) -> list :
        """Returns list of operands if all checks are valid"""
        if len(operands) > len(words):
            raise ParsingFailure('Not enough operands')
        if len(operands) == 1:
            result = operands[0].check(words[0])
            if result is None:
                raise ParsingFailure('No valid operands')
            else: return [result]
        else:
            for possible_options in combinations(words):
                result1 = operands[0].check(' '.join(possible_options[0]))
                result2 = operands[1].check(' '.join(possible_options[1]))
                if result1 is not None and result2 is not None:
                    break
            else:  # (nobreak)
                raise ParsingFailure('No valid operands')
            return [result1, result2]

class Parser:

    def __init__(self, *parsers: ParserCase):
        self.parsers=[]
        for parser in parsers:
            self.parsers.append(parser)

    @property
    def parser_count(self):
        return len(self.parsers)

    def parse(self, string):
        for parser in self.parsers:
            try:
                return parser.parse(string)
            except ParsingFailure:
                continue
        return f"Can't parse '{string}'"





if __name__ == '__main__':



    pass

