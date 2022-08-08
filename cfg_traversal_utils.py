from functools import cached_property
from typing import Dict

import networkx as nx

from slither_ir_ply import SlitherIR


class CFGPath:
    def __init__(self, cfg: nx.MultiDiGraph, *args):
        self.cfg = cfg
        self.nodes = args

        self.variable_table: Dict[str, int] = {}

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
    def constraints(self):
        return [SlitherIR(expr).constraints for expr in self.expressions]

    @cached_property
    def is_sat(self):
        raise NotImplementedError  # TODO Should implement
