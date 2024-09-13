import logging
import re
import time
from functools import cached_property, partial
from typing import List

import ply.lex as lex
import ply.yacc as yacc
from manticore.ethereum.abitypes import lexer as type_lexer
from manticore.exceptions import EthereumError
from z3 import BitVecVal, BoolVal, Bool, And, Or, Not, Function, IntSort, BoolSort, Int, ForAll, \
    Implies, BitVec, ULT, UGT, ULE, UGE, UDiv, URem, BitVecSort, String

logger = logging.getLogger('SlitherIRPLY')

# Reserved Keywords
reserved = {
    'RETURN': 'RETURN',
    'CONDITION': 'CONDITION',
    'SOLIDITY_CALL': 'SOLIDITY_CALL',
    'CONVERT': 'CONVERT',
    'to': 'TO',

    'INITIALIZE_GLOBS': 'INITIALIZE_GLOBS',
    'INITIALIZE_FUNC_PARAMS': 'INITIALIZE_FUNC_PARAMS',
    'TRANSACTION_STARTS': 'TRANSACTION_STARTS',

    'NOT': 'NOT',
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

    # Indexing/Membership Operators
    'ARROW',
    'DOT',

    # Binary Operations
    # https://github.com/crytic/slither/wiki/SlithIR#binary-operation
    'EQUAL',
    'COND_EQUAL',
    'COND_INEQUALITY',
    'MATH_OPS',  # Math Binary Operators
    'UNARY_OPS',  # Boolean Unary Operators
    'BINARY_BOOLEAN_OPS',  # Boolean Binary Operators

    # Parenthesis, Brackets, etc.
    'LPAREN',
    'RPAREN',
    'LBRACKETS',
    'RBRACKETS',

    # Types
    # From Manticore https://github.com/trailofbits/manticore/blob/master/manticore/ethereum/abitypes.py
    'UINT',
    'UINTN',
    'INTN',
    'BOOL',
    'STRING',
    'ADDRESS',

    'COMMA',
    'VOID',
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
    if t.value == 'None':
        t.type = "VOID"
    if t.value == 'string':
        t.type = "STRING"
    if t.type == 'ADDRESS':
        t.value = 'ADDRESS'

    return t


# noinspection PyPep8Naming
def t_NUMBER(t):
    r"""\d+"""
    t.value = int(t.value)
    return t


# noinspection PyPep8Naming
def t_LPAREN_C_RPAREN(t):
    r"""\(c\)"""
    pass  # TODO: Maybe do not ignore this token


# Assignment
# https://github.com/crytic/slither/wiki/SlithIR#assignment
t_ASSIGNMENT = r':='

# Binary Operations
# https://github.com/crytic/slither/wiki/SlithIR#binary-operation
t_EQUAL = r'='
t_COND_EQUAL = r'=='
t_COND_INEQUALITY = r'(<=)|(>=)|<|>|!='
t_MATH_OPS = r'\-(?!>)|\+|\*|\/|%'
t_UNARY_OPS = r'\!|\~'
t_BINARY_BOOLEAN_OPS = r'(\&\&)|(\|\|)'

# Indexing/Membership Operators
t_ARROW = r'->'
t_DOT = r'\.'

# Ignore
t_ignore = ' \t'

# Parenthesis, Brackets, etc
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACKETS = r'\['
t_RBRACKETS = r'\]'

t_COMMA = r','


def t_error(t):
    pass  # TODO: Should implement later.


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

    def get_variable(self, symbol_name, plus_plus=False, save=False) -> str:
        # TODO: Change name of this function to get indexed variable
        if plus_plus:
            if save is False:
                return f"{symbol_name}_{self.__symbols.get(symbol_name, -1) + 1}"
            else:
                self.__symbols[symbol_name] = self.__symbols.get(symbol_name, -1) + 1
                return f"{symbol_name}_{self.__symbols[symbol_name]}"

        return f"{symbol_name}_{self.__symbols.get(symbol_name, 0)}"

    @property
    def get_mapping_references(self):
        return [k for k, v in self.__types.items() if ('mapping' in v and k.startswith('REF_'))]

    @classmethod
    def __z3_sorts(cls, variable_type):
        if "int" in variable_type:
            return BitVecSort(sz=int(variable_type.replace("uint", "").replace("int", "")))
        else:
            return {
                'bool': BoolSort(),
                'address': BitVecSort(sz=256),  # TODO Even better sort
            }.get(variable_type)

    @classmethod
    def z3_types(cls, variable_type):
        if variable_type.startswith("uint"):
            return partial(BitVec, bv=int(variable_type.replace("uint", "")))
        elif variable_type.startswith("int"):
            return partial(BitVec, bv=int(variable_type.replace("int", "")))
        elif variable_type.startswith("bv"):
            return partial(BitVec, bv=int(variable_type.replace("bv", "")))
        elif variable_type == 'string':
            return String
        elif variable_type.startswith("REF"):
            raise NotImplementedError
        else:
            return {
                'bool': Bool,
                'address': partial(BitVec, bv=256),
            }.get(variable_type)

    @classmethod
    def get_z3_references(cls, variable_type):
        if 'mapping' in variable_type:
            matched = re.match(
                r"REF\[mapping\((?P<mapping_from>\w+)\s?=>\s?"
                r"(?P<mapping_to>\w+)\),\s(?P<referee>\w+),\s(?P<index>[\w\.]+)]",
                variable_type
            )
            return (
                Function(
                    matched.group("referee"),
                    cls.__z3_sorts(matched.group("mapping_from")),
                    IntSort(),  # CAUTION: For the SSA
                    cls.__z3_sorts(matched.group("mapping_to"))
                ),
                matched.group("index")
            )
        else:
            pass  # TODO: e.g. we do not support 2d mapping now

    def get_z3_variable(self, symbol_name, plus_plus=False, save=False):
        if symbol_name.startswith("REF_"):  # References
            func, indx = self.get_z3_references(self.__types[symbol_name])
            index_of_reference = self.get_variable(
                func.name(), plus_plus=plus_plus, save=save
            ).removeprefix(func.name()).replace("_", "")
            if indx.isnumeric() is True:
                return func(indx, index_of_reference)
            else:
                return func(self.get_z3_variable(indx, plus_plus=False, save=False), index_of_reference)
        else:
            return self.z3_types(self.__types[symbol_name])(
                self.get_variable(symbol_name, plus_plus=plus_plus, save=save)
            )

    def get_z3_all_except_reference_conds(self, symbol_name, plus_plus=False, save=False):
        if not symbol_name.startswith('REF_'):
            raise NotImplementedError

        func, indx = self.get_z3_references(self.__types[symbol_name])
        from_sort = func.domain(0)
        if from_sort.name().lower() == "bv":
            temp_variable = self.z3_types(f"{from_sort.name().lower()}{from_sort.size()}")(
                f"mapping_temp_{time.time_ns()}"
            )
        else:
            temp_variable = self.z3_types(from_sort.name().lower())(f"mapping_temp_{time.time_ns()}")

        index_of_reference = self.get_variable(
            func.name(), plus_plus=plus_plus, save=save
        ).removeprefix(func.name()).replace("_", "")

        # return func(temp_variable, index_of_reference) == func(temp_variable, str(int(index_of_reference) + 1))
        if indx.isnumeric():
            return ForAll(
                [temp_variable],
                Implies(
                    temp_variable != indx,
                    func(temp_variable, index_of_reference) == func(temp_variable, str(int(index_of_reference) + 1))
                )
            )
        else:
            return ForAll(
                [temp_variable],
                Implies(
                    temp_variable != self.get_z3_variable(indx, plus_plus=False, save=False),
                    func(temp_variable, index_of_reference) == func(temp_variable, str(int(index_of_reference) + 1))
                )
            )

    def set_types(self, types):
        self.__types = {
            **types,
            'msg.sender': 'address',
            'msg.value': 'uint256'
        }

    def clear_table(self):
        self.__symbols = {}
        self.__types = {}

    @property
    def symbols(self):
        return self.__symbols


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
    logger.error(
        f'Syntax error while processing '
        f'token={p.type}, '
        f'value={p.value}, '
        f'lineno={p.lineno}, '
        f'pos={p.lexpos}, '
        f'lex_data="{p.lexer.lexdata}"'
    )
    raise SlitherIRSyntaxError(p)


def p_type(p: yacc.YaccProduction):
    """type : BOOL
            | UINT
            | UINTN
            | INTN
            | VOID
            | STRING
            | ADDRESS"""
    p[0] = p[1]


def p_return_stmt(p):
    """expression : RETURN
                  | RETURN bin_op_rvalue"""
    p[0] = BoolVal(True)  # no constraint for return statements


def p_constant(p):
    """constant : NUMBER"""
    # TODO Other Types
    p[0] = BitVecVal(p[1], bv=256).as_long()


def p_assignment(p):
    """expression : ID LPAREN type RPAREN ASSIGNMENT bin_op_rvalue LPAREN type RPAREN"""
    #       0        1    2    3     4        5       6               7     8     9
    if p[3] != p[8] and type(p[6][1]) != int:
        raise SlitherIRSyntaxError(p)

    if p[6][0] != 'const':  # It's a variable/reference
        p[0] = symbol_table_manager.get_z3_variable(p[1], plus_plus=True, save=True)
        _p6 = symbol_table_manager.get_z3_variable(p[6][1], plus_plus=True)
        p[0] = p[0] == _p6
    else:
        p[0] = symbol_table_manager.get_z3_variable(p[1], plus_plus=True, save=True)
        p[0] = p[0] == p[6][1]


def p_binary_operator(p):
    """bin_op : COND_INEQUALITY
              | COND_EQUAL
              | MATH_OPS
              | BINARY_BOOLEAN_OPS"""
    p[0] = p[1]


def p_binary_operation_rvalue(p):
    """bin_op_rvalue : ID
                     | ID DOT ID
                     | constant"""
    if len(p) == 4:
        p[0] = ('builtin', ''.join(p[1:]))  # TODO better implementation for custom classes
    elif isinstance(p[1], int):  # TODO Other constant types
        p[0] = ('const', p[1])
    elif p[1] in ["True", "False"]:
        p[0] = ('const', BoolVal(True) if p[1] == "True" else BoolVal(False))
    elif p[1].startswith("REF_"):
        p[0] = ('reference', p[1])
    else:
        p[0] = ('symbol', p[1])


def _rvalue_processor(rvalue):
    if rvalue[0] == 'const':
        return rvalue[1]
    elif rvalue[1] == "True":
        return BoolVal(True)
    elif rvalue[1] == "False":
        return BoolVal(False)
    else:  # References and Symbols
        return symbol_table_manager.get_z3_variable(rvalue[1], plus_plus=True)


# https://github.com/crytic/slither/wiki/SlithIR#binary-operation
def p_binary_operation(p):
    """expression : ID LPAREN type RPAREN EQUAL bin_op_rvalue bin_op bin_op_rvalue"""
    #      0        1    2     3      4     5         6         7          8
    if p[3][0].startswith("uint"):
        funcs = {
            '<': ULT,
            '>': UGT,
            '<=': ULE,
            '>=': UGE,
            '-': lambda a, b: a - b,
            '+': lambda a, b: a + b,
            '*': lambda a, b: a * b,
            '%': URem,
            '/': UDiv,
        }
    else:
        funcs = {
            '<': lambda a, b: a < b,
            '>': lambda a, b: a > b,
            '<=': lambda a, b: a <= b,
            '>=': lambda a, b: a >= b,
            '-': lambda a, b: a - b,
            '+': lambda a, b: a + b,
            '*': lambda a, b: a * b,
            '%': lambda a, b: a % b,
            '/': lambda a, b: a / b,
        }

    funcs.update({
        '==': lambda a, b: a == b,
        '&&': lambda a, b: And(a, b),
        '||': lambda a, b: Or(a, b),
        '!=': lambda a, b: a != b,
    })
    operation = funcs.get(p[7])

    p[0] = symbol_table_manager.get_z3_variable(p[1], plus_plus=True, save=True)
    p[0] = p[0] == operation(
        _rvalue_processor(rvalue=p[6]),
        _rvalue_processor(rvalue=p[8]),
    )


def p_unary_operation(p):
    """expression : ID EQUAL UNARY_OPS bin_op_rvalue"""
    #      0         1  2        3     4
    p[0] = symbol_table_manager.get_z3_variable(p[1], plus_plus=True, save=True)
    operation = {
        '!': lambda v: Not(v),  # TODO Support `~`
    }.get(p[3])

    p[0] = p[0] == operation(_rvalue_processor(p[4]))


def p_condition(p):
    """expression : CONDITION ID
                  | CONDITION constant
                  | CONDITION NOT ID
                  | CONDITION NOT constant"""
    if len(p) == 4 and p[2] == 'NOT' and isinstance(p[3], str):  # CONDITION NOT ID
        smt_variable = symbol_table_manager.get_z3_variable(p[3], plus_plus=True)
        p[0] = smt_variable == BoolVal(False)
    elif isinstance(p[2], str):  # CONDITION ID
        smt_variable = symbol_table_manager.get_z3_variable(p[2], plus_plus=True)
        p[0] = smt_variable == BoolVal(True)
    else:
        pass


def p_index(p):
    """expression : ID LPAREN type RPAREN ARROW ID LBRACKETS bin_op_rvalue RBRACKETS"""
    p[0] = BoolVal(True)  # Parsed before in variables finding


def p_mapping_assignment(p):
    """expression : ID LPAREN ARROW ID RPAREN ASSIGNMENT bin_op_rvalue LPAREN type RPAREN"""
    #               1               4                         7
    if isinstance(p[7], tuple):  # It's a variable
        p[0] = symbol_table_manager.get_z3_variable(p[1], plus_plus=True, save=True)
        if p[7][0] == "const":
            _p7 = p[7][1]
        elif p[7][0] == "symbol" and p[7][1] in ["True", "False"]:
            _p7 = p[7][1] == "True"
        else:
            _p7 = symbol_table_manager.get_z3_variable(p[7][1], plus_plus=True)
        p[0] = p[0] == _p7
    else:
        p[0] = symbol_table_manager.get_z3_variable(p[1], plus_plus=True, save=True)
        p[0] = p[0] == p[7]

    p[0] = And(p[0], symbol_table_manager.get_z3_all_except_reference_conds(p[1]))


def init_msg(p):
    # Only for changing the msg index in each transaction
    msg_sender = symbol_table_manager.get_z3_variable('msg.sender', plus_plus=True, save=True)
    p[0] = And(p[0], Or(
        msg_sender == BitVecVal(0x1111111111111111111111111111111111111111, bv=256),
        msg_sender == BitVecVal(0x2222222222222222222222222222222222222222, bv=256),
        msg_sender == BitVecVal(0x3333333333333333333333333333333333333333, bv=256),
        msg_sender == BitVecVal(0x4444444444444444444444444444444444444444, bv=256),
        msg_sender == BitVecVal(0x5555555555555555555555555555555555555555, bv=256),
    ))
    p[0] = And(p[0], symbol_table_manager.get_z3_variable('msg.value', plus_plus=True, save=True) >= 0)


def p_initialize_globals(p):
    """expression : INITIALIZE_GLOBS"""
    p[0] = BoolVal(True)
    for reference_name in symbol_table_manager.get_mapping_references:
        p[0] = And(p[0], symbol_table_manager.get_z3_variable(reference_name, plus_plus=True, save=False) == 0)

    init_msg(p)


def p_transaction_starts(p):
    """expression : TRANSACTION_STARTS"""
    p[0] = BoolVal(True)

    init_msg(p)


def p_initialize_func_params(p):
    """expression : INITIALIZE_FUNC_PARAMS ID"""
    #      0                1              2
    p[0] = BoolVal(True)

    symbol_table_manager.get_z3_variable(p[2], plus_plus=True, save=True)


def p_type_list(p):
    """type_list : type COMMA type_list
                 | type"""
    #     0          1    2       3
    if len(p) == 2:
        p[0] = [p[1], ]
    else:
        p[0] = [p[1], *p[3]]


def p_func_string_param(p):
    """func_string_param : ID func_string_param
                         | ID
                         | DOT"""
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = f"{p[1]} {p[2]}"


def p_rvalue_list(p):
    """rvalue_list : bin_op_rvalue COMMA rvalue_list
                   | func_string_param COMMA rvalue_list
                   | bin_op_rvalue
                   | func_string_param"""
    if len(p) == 2:
        p[0] = [p[1], ]
    else:
        p[0] = [p[1], *p[3]]


def p_solidity_call(p):
    """expression : ID LPAREN type RPAREN EQUAL SOLIDITY_CALL ID LPAREN type_list RPAREN LPAREN rvalue_list RPAREN"""
    #      0        1     2    3     4      5         6       7    8       9        10     11        12       13
    p[0] = {
        "require": lambda params, declaration: _rvalue_processor(params[0]) == BoolVal(True),
        "assert": lambda params, declaration: _rvalue_processor(params[0]) == BoolVal(True),
        "revert": lambda params, declaration: BoolVal(True),
    }.get(p[7])(params=p[12], declaration=p[9])


def p_convert(p):
    """expression : ID EQUAL CONVERT bin_op_rvalue TO type"""
    #      0        1    2      3      4     5   6
    if p[6] == 'ADDRESS':
        p[0] = symbol_table_manager.get_z3_variable(p[1], plus_plus=True, save=True)
        if p[4][0] != 'const':
            _p4 = symbol_table_manager.get_z3_variable(p[4][1], plus_plus=True)
            p[0] = p[0] == _p4
        else:
            p[0] = p[0] == p[4][1]
    else:
        raise  # TODO: Others


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
        if self.expr.startswith("Emit"):  # TODO Add more to-ignore expressions
            return []
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
