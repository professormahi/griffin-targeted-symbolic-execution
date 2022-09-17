import re
from functools import cached_property

import networkx as nx
from z3 import Solver, sat

from slither_ir_ply import SlitherIR, SymbolTableManager


class CFGPath:
    def __init__(self, cfg: nx.MultiDiGraph, *args, **kwargs):
        self.cfg = cfg
        self.nodes = args

        self._variables = kwargs.get('variables', None)

    def __get_irs(self, node):
        return self.cfg.nodes[node].get("irs", [])

    def __get_reversed_irs(self, node):
        return list(reversed(self.__get_irs(node)))

    @cached_property
    def expressions(self):
        res = []
        for node in self.nodes:
            res.extend(self.__get_reversed_irs(node))  # Reversing is required to have correct backward path
        return res

    @cached_property
    def variables(self):
        result = self._variables or {}

        # Variables from IRs
        compiled_pattern = re.compile(r"^(?P<variable_name>\w+)\((?P<variable_type>\w+)\)\s(=|:=)")
        for expr in self.expressions:
            if matched := compiled_pattern.match(expr):
                result[matched.group("variable_name")] = matched.group("variable_type")

        return result

    @cached_property
    def constraints(self):
        SymbolTableManager.get_instance().set_types(self.variables)

        return [SlitherIR(expr).constraints for expr in self.expressions]

    @cached_property
    def solver(self):
        solver = Solver()
        for constraint in self.constraints:
            solver.add(constraint)
        return solver

    @cached_property
    def is_sat(self):
        return self.solver.check() == sat

    @cached_property
    def sat_inputs(self):
        if self.is_sat is False:
            return []
        else:
            return self.solver.model()
