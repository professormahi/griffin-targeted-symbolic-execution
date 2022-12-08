import re
from functools import cached_property
from typing import Callable

import networkx as nx
from z3 import Solver, sat

import utils
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

        # There is bug in SlitherIR that for `rvalue = ! lvalue` and `rvalue = ~ lvalue` no type is applied
        # TODO: Add issue to Slither and fix this. After that, we should remove the following loop
        compiled_pattern = re.compile(r"^(?P<variable_name>\w+)\s?=\s?[!~]\s(\w+)")
        for expr in self.expressions:
            if matched := compiled_pattern.match(expr):
                result[matched.group("variable_name")] = 'bool'

        return result

    @cached_property
    def constraints(self):
        SymbolTableManager.get_instance().clear_table()
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


class Heuristic:
    @staticmethod
    def get_instance(graph: nx.MultiDiGraph, name: str = "floyd_warshall"):
        return {
            "floyd_warshall": FloydWarshall
        }.get(name)(graph)

    def __init__(self, graph: nx.MultiDiGraph):
        self._graph = graph

    def fitness(self, s: str, t: str):
        raise NotImplementedError


class FloydWarshall(Heuristic):
    def __init__(self, graph: nx.MultiDiGraph):
        super().__init__(graph)

        self.__floyd_warshall_result = nx.floyd_warshall(self._graph)

    def fitness(self, s: str, t: str):
        return self.__floyd_warshall_result[s][t]


class WalkTree:
    def __init__(self, contract, reversed_cfg: nx.MultiDiGraph, target_node: str, entry_point: str = 'START_NODE'):
        self.contract = contract
        self.reversed_cfg = reversed_cfg
        self.target_node = target_node
        self.entry_point = entry_point

        self.__walk_tree = nx.DiGraph()
        self.__last_node = -1
        self.__add_node(self.target_node)  # Add the walk-tree root

        # TODO: Use better data-structure for __frontiers later. Maybe min-heap
        self.__frontiers = [0, ]  # Only the target node for start

    def __add_node(self, node_name: str, parent: int = None) -> int:
        self.__last_node += 1

        self.__walk_tree.add_node(self.__last_node, name_on_rev_cfg=node_name)

        if parent is not None:  # Add edge to parent if not root
            self.__walk_tree.add_edge(u_of_edge=parent, v_of_edge=self.__last_node)

        return self.__last_node

    @cached_property
    def __heuristic(self) -> Callable:
        from arg_parser import args

        return Heuristic.get_instance(self.reversed_cfg, name=args.heuristic).fitness

    def __get_node_on_rev_cfg(self, walk_node_id) -> str:
        return self.__walk_tree.nodes[walk_node_id]['name_on_rev_cfg']

    @property
    def __next_best_option(self):
        return min(
            self.__frontiers,
            key=lambda item: self.__heuristic(self.__get_node_on_rev_cfg(item), self.entry_point),
        )

    def __cfg_path_for(self, walk_node_id: int) -> CFGPath:
        return CFGPath(
            self.reversed_cfg,
            *[
                self.__get_node_on_rev_cfg(__walk_node_id)
                for __walk_node_id in nx.shortest_path(self.__walk_tree, target=walk_node_id, source=0)
            ],
            variables=self.contract.variables
        )

    def traverse(self) -> CFGPath | None:
        while True:
            option = self.__next_best_option
            option_name = self.__get_node_on_rev_cfg(option)
            self.__frontiers.remove(option)  # TODO: Maybe better implementation; This O(n) now.

            cfg_path = self.__cfg_path_for(option)

            utils.log(f"Extending {option_name}", level='debug')
            for i in range(len(cfg_path.expressions)):
                utils.log(
                    f"option={option_name} # {cfg_path.expressions[i].ljust(50)} {cfg_path.constraints[i]}",
                    level='debug',
                )
            utils.log(f"option={option_name} # Is Sat? {cfg_path.is_sat}", level='debug')
            utils.log(f"option={option_name} # Sat inputs: {cfg_path.sat_inputs}", level='debug')

            if cfg_path.is_sat:
                if self.__get_node_on_rev_cfg(option) == self.entry_point:
                    utils.log(
                        f"option={option_name} # There is a SAT path to entry point with inputs: {cfg_path.sat_inputs}",
                        level='debug',
                    )
                    return cfg_path
                else:  # SAT but not the full walk from target to entry point
                    for neighbor in self.reversed_cfg.neighbors(self.__get_node_on_rev_cfg(option)):
                        node_id = self.__add_node(neighbor, parent=option)
                        self.__frontiers.append(node_id)

            if self.__frontiers.__len__() == 0:
                return None
