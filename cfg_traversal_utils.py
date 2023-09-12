import re
from functools import cached_property
from typing import Callable, Optional, List

import networkx as nx
from z3 import Solver, sat

import utils
from slither_ir_ply import SlitherIR, SymbolTableManager, symbol_table_manager


class CFGPath:
    def __init__(self, cfg: nx.MultiDiGraph, *args, **kwargs):
        self.cfg = cfg
        self.nodes = args

        self._variables = kwargs.get('variables', None)

    def __get_irs(self, node):
        return self.cfg.nodes[node].get("irs", [])

    def __get_reversed_irs(self, node):
        return list(reversed(self.__get_irs(node)))

    def __get_prev_edge(self, node_index: int) -> Optional[str]:
        if node_index == 0:
            return None
        return self.cfg.get_edge_data(
            self.nodes[node_index - 1],
            self.nodes[node_index],
        )[0]['label']

    @cached_property
    def expressions(self):
        res = []
        for indx, node in enumerate(self.nodes):
            # TODO: Also do this about for statements
            if self.cfg.nodes[node].get('node_type') == "IF" and self.__get_prev_edge(indx) == 'False':
                res.extend(
                    map(
                        lambda expr: expr if 'CONDITION' not in expr else expr.replace("CONDITION", "CONDITION NOT"),
                        self.__get_reversed_irs(node),
                    )
                )
            else:
                res.extend(self.__get_reversed_irs(node))  # Reversing is required to have correct backward path
        return res

    @cached_property
    def variables(self):
        return self._variables

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
            model = self.solver.model()
            return {value.name(): model[value] for value in model}

    @cached_property
    def txs(self) -> List | None:
        if self.is_sat is False:
            return None

        _txs = []
        _nodes = list(reversed(list(self.nodes)))
        _symbols = symbol_table_manager.symbols.copy()
        for prev, cur, nxt in zip(_nodes, _nodes[1:], _nodes[2:]):
            # TODO: Maybe add default constructor
            if prev in ['AFTER_CREATION', "START_NODE"] and cur != "AFTER_CREATION":
                params = self.cfg.nodes[cur].get("params") or []
                params = [*params, 'msg.sender', 'msg.value']
                params_values = {param: self.sat_inputs.get(f"{param}_{_symbols[param]}", "any") for param in params}
                for param in params:
                    _symbols[param] -= 1

                _txs.append({
                    'function': cur.split("_")[0],
                    'params': params_values
                })

        return _txs

    @cached_property
    def not_written_variables(self) -> List:
        rw = {}
        for node in self.nodes:
            for var in self.cfg.nodes[node].get('state_variables_read', []):
                if var not in rw.keys():
                    rw[var] = 0
                rw[var] += 1
            for var in self.cfg.nodes[node].get('state_variables_written', []):
                rw[var] = 0
        return [var for var in rw.keys() if rw[var] > 0]


class Heuristic:
    @staticmethod
    def get_instance(graph: nx.MultiDiGraph, name: str = "floyd_warshall"):
        return {
            "floyd_warshall": FloydWarshall,
            "state_variables_based": StateVariablesBasedHeuristic,
        }.get(name)(graph)

    def __init__(self, graph: nx.MultiDiGraph):
        self._graph = graph

    def fitness(self, s: str, t: str, **extra):
        raise NotImplementedError


class FloydWarshall(Heuristic):
    def __init__(self, graph: nx.MultiDiGraph):
        super().__init__(graph)

        self._floyd_warshall_result = nx.floyd_warshall(self._graph)

    def fitness(self, s: str, t: str, **extra):
        return self._floyd_warshall_result[s][t]


class StateVariablesBasedHeuristic(FloydWarshall):
    def __init__(self, graph: nx.MultiDiGraph):
        super().__init__(graph)

    def fitness(self, s: str, t: str, **extra):
        current_walk: CFGPath = extra.get('current_walk')
        if s in list(self._graph.neighbors('AFTER_TX')) and current_walk.not_written_variables is not None:
            if not current_walk.not_written_variables or (
                    set(current_walk.not_written_variables) &
                    set(self._graph.nodes[s].get('func_state_variables_written'))
            ):
                return self._floyd_warshall_result[s][t]
            else:
                return float('inf')
        return self._floyd_warshall_result[s][t]


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
        utils.log(f"Heuristic {args.heuristic}", level='debug')

        return Heuristic.get_instance(self.reversed_cfg, name=args.heuristic).fitness

    def __get_node_on_rev_cfg(self, walk_node_id) -> str:
        return self.__walk_tree.nodes[walk_node_id]['name_on_rev_cfg']

    @property
    def __next_best_option(self):
        return min(
            self.__frontiers,
            key=lambda item: self.__heuristic(
                self.__get_node_on_rev_cfg(item),
                self.entry_point,
                current_walk=self.__cfg_path_for(item),  # TODO: Better performance
            ),
        )

    def __cfg_path_for(self, walk_node_id: int) -> CFGPath:
        return CFGPath(
            self.reversed_cfg,
            *[
                self.__get_node_on_rev_cfg(__walk_node_id)
                for __walk_node_id in nx.shortest_path(self.__walk_tree, target=walk_node_id, source=0)
            ],
            variables=self.__contract_variables,
        )

    @cached_property
    def __contract_variables(self):
        # The contract variables
        variables = self.contract.variables

        # The IR variables
        compiled_pattern = re.compile(r"^(?P<variable_name>\w+)\((?P<variable_type>\w+)\)\s(=|:=|->)")
        for node in self.contract.cfg.nodes:
            for expr in self.contract.cfg.nodes[node].get("irs", []):
                if matched := compiled_pattern.match(expr):
                    if matched.group("variable_name").startswith("REF_") is False:
                        variables[matched.group("variable_name")] = matched.group("variable_type")
                    elif rvalue_matched := re.match(
                            r"\w+\(\w+\)\s?->\s?(?P<referee_name>\w+)\[(?P<index>[\w\.]+)]",
                            expr
                    ):
                        referee_name = rvalue_matched.group('referee_name')
                        indx = rvalue_matched.group('index')
                        variables[matched.group("variable_name")] = f'REF[{variables[referee_name]}, {referee_name}, ' \
                                                                    f'{indx}]'
                    else:
                        pass  # TODO REF_i -> REF_j.member

        # There is bug in SlitherIR that for `rvalue = ! lvalue` and `rvalue = ~ lvalue` no type is applied
        # TODO: Add issue to Slither and fix this. After that, we should remove the following loop
        compiled_pattern = re.compile(r"^(?P<variable_name>\w+)\s?=\s?[!~]\s(\w+)")
        for node in self.contract.cfg.nodes:
            for expr in self.contract.cfg.nodes[node].get("irs", []):
                if matched := compiled_pattern.match(expr):
                    variables[matched.group("variable_name")] = 'bool'

        return variables

    def traverse(self) -> CFGPath | None:
        while True:
            option = self.__next_best_option
            option_name = self.__get_node_on_rev_cfg(option)
            self.__frontiers.remove(option)  # TODO: Maybe better implementation; This O(n) now.

            cfg_path = self.__cfg_path_for(option)

            utils.log(f"Extending {option_name}", level='debug')
            utils.log(f"The new path is {cfg_path.nodes}", level='debug')
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
