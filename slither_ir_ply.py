import logging
from functools import cached_property, partial
from typing import List

import ply.lex as lex
import ply.yacc as yacc
from z3 import BitVec, BitVecVal, BoolVal, Bool, BitVecNumRef
from manticore.ethereum.abitypes import lexer as type_lexer
from manticore.exceptions import EthereumError

logger = logging.getLogger('SlitherIRPLY')

# Reserved Keywords
reserved = {
    'input': 'INPUT',

    'RETURN': 'RETURN',
    'CONDITION': 'CONDITION',
}

# Lex Tokens
tokens = [
    # Variables
    # https://github.com/crytic/slither/wiki/SlithIR#variables
    'ID',
    'NUMBER',

    # Assignment
    # https://github.com/crytic/slither/wiki/SlithIR#assignment
    'ASSIGNMENT',

    # Binary Operations
    # https://github.com/crytic/slither/wiki/SlithIR#binary-operation
    'EQUAL',
    'COND_EQUAL',
    'COND_LESS',

    # Parenthesis
    'LPAREN',
    'RPAREN',

    # Types
    # From Manticore https://github.com/trailofbits/manticore/blob/master/manticore/ethereum/abitypes.py
    'UINT',
    'UINTN',
    'BOOL',
]
tokens.extend(list(reserved.values()))  # Add reserved keywords to tokens


# Variables
# https://github.com/crytic/slither/wiki/SlithIR#variables
# noinspection PyPep8Naming
def t_ID(t):
    r"""[a-zA-Z_][a-zA-Z_0-9]*"""
    t.type = reserved.get(t.value, 'ID')  # Check for reserved words

    # Check for type tokens using manticore lexer
    # https://github.com/trailofbits/manticore/blob/master/manticore/ethereum/abitypes.py
    try:
        type_lexer.input(t.value)
        type_token = type_lexer.token()
        if type_token:
            t.type = type_token.type
            t.value = type_token.value
    except EthereumError:  # Do nothing if this is not a type token
        pass

    return t


# noinspection PyPep8Naming
def t_NUMBER(t):
    r"""\d+"""
    t.value = int(t.value)
    return t


# Assignment
# https://github.com/crytic/slither/wiki/SlithIR#assignment
t_ASSIGNMENT = r':='

# Binary Operations
# https://github.com/crytic/slither/wiki/SlithIR#binary-operation
t_EQUAL = r'='
t_COND_EQUAL = r'=='
t_COND_LESS = r'<'

# Ignore
t_ignore = ' \t'

# Parenthesis
t_LPAREN = r'\('
t_RPAREN = r'\)'

IR_LEXER = lex.lex()  # TODO Add more lex patterns


class SymbolTableManager:
    __instance = None

    def __init__(self):
        if self.__instance is not None:
            raise NotImplementedError

        self.__symbols = {}
        self.__types = {}

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = SymbolTableManager()

        return cls.__instance

    def get_variable(self, symbol_name, new=False) -> str:
        if new is True:
            self.__symbols[symbol_name] = self.__symbols.get(symbol_name, -1) + 1

        return f"{symbol_name}_{self.__symbols.get(symbol_name, 0)}"

    @staticmethod
    def z3_types(variable_type):
        if variable_type.startswith("uint"):
            return partial(BitVec, bv=int(variable_type[4:]))
        elif variable_type.startswith("int"):
            return partial(BitVec, bv=int(variable_type[3:]))
        else:
            return {
                'bool': Bool,
            }.get(variable_type)

    def get_z3_variable(self, symbol_name, new=False):
        return self.z3_types(self.__types[symbol_name])(self.get_variable(symbol_name, new))

    def set_types(self, types):
        self.__types = types

    def clear_table(self):
        self.__symbols = {}
        self.__types = {}


symbol_table_manager = SymbolTableManager.get_instance()


class SlitherIRSyntaxError(Exception):
    def __init__(self, p):
        self.token = p.type
        self.value = p.value
        self.lineno = p.lineno
        self.pos = p.lexpos

    def __str__(self):
        return f'Syntax error while processing token={self.token}, value={self.value}, lineno={self.lineno}, pos={self.pos}'


def p_error(p):
    logger.error(f'Syntax error while processing token={p.type}, value={p.value}, lineno={p.lineno}, pos={p.lexpos}')
    raise SlitherIRSyntaxError(p)


def p_type(p: yacc.YaccProduction):
    """type : BOOL
            | UINT
            | UINTN"""
    p[0] = p[1]


def p_return_stmt(p):
    """expression : RETURN
                  | RETURN ID"""
    p[0] = BoolVal(True)  # no constraint for return statements


def p_constant(p):
    """constant : NUMBER"""
    # TODO Other Types
    p[0] = BitVecVal(p[1], bv=256)


def p_assignment(p):
    """expression : ID LPAREN type RPAREN ASSIGNMENT constant LPAREN type RPAREN
                  | ID LPAREN type RPAREN ASSIGNMENT ID LPAREN type RPAREN"""
    #       0        1    2    3     4        5       6       7     8     9
    if p[3] != p[8]:
        raise SlitherIRSyntaxError(p)

    if isinstance(p[6], str):
        p[0] = symbol_table_manager.get_z3_variable(p[1])
        _p6 = symbol_table_manager.get_z3_variable(p[6])
        p[0] = p[0] == _p6
    else:
        p[0] = symbol_table_manager.get_z3_variable(p[1], new=True)
        p[0] = p[0] == p[6]


def p_binary_operator(p):
    """bin_op : COND_LESS
              | COND_EQUAL"""
    p[0] = p[1]


def p_binary_operation_rvalue(p):
    """bin_op_rvalue : ID
                     | constant"""
    if isinstance(p[1], BitVecNumRef):  # TODO Other constant types
        p[0] = p[1]
    else:
        p[0] = symbol_table_manager.get_z3_variable(p[1])


# https://github.com/crytic/slither/wiki/SlithIR#binary-operation
def p_binary_operation(p):
    """expression : ID LPAREN type RPAREN EQUAL bin_op_rvalue bin_op bin_op_rvalue"""
    #      0        1    2     3      4     5         6         7          8
    operation = {
        '<': lambda a, b: a < b,
        '==': lambda a, b: a == b,
    }.get(p[7])

    p[0] = symbol_table_manager.get_z3_variable(p[1], new=True)
    p[0] = p[0] == operation(p[6], p[8])


def p_condition(p):
    """expression : CONDITION ID
                  | CONDITION constant"""
    if isinstance(p[2], str):  # CONDITION ID
        smt_variable = symbol_table_manager.get_z3_variable(p[2])
        p[0] = smt_variable == BoolVal(True)
    else:
        pass


IR_PARSER = yacc.yacc(start="expression")  # TODO Add more yacc patterns


class SlitherIR:
    """
    https://github.com/crytic/slither/wiki/SlithIR#slithir-specification
    """

    def __init__(self, ir_expr):
        self.expr = ir_expr

    @cached_property
    def tokens(self) -> List[lex.LexToken]:
        IR_LEXER.input(self.expr)

        res = []
        while (token := IR_LEXER.token()) is not None:
            res.append(token)
        return res

    @cached_property
    def constraints(self):
        return IR_PARSER.parse(self.expr, lexer=IR_LEXER)


if __name__ == '__main__':  # For testing the PLY
    for example in [
        'RETURN result',
        'CONDITION TMP_4',
        'TMP_4(bool) = result == 150',
        'CONDITION TMP_2',
        'TMP_2(bool) = i < 100',
        'result(uint256) := input(uint256)',
        'sellerBalance(uint256) := 0(uint256)',
    ]:
        print(f"{example}: ", IR_PARSER.parse(example, lexer=IR_LEXER))
