import json
import re
from functools import cached_property
from typing import Union, List

import networkx as nx
import solcx
from evm_cfg_builder import CFG as EVMCFG
from pyevmasm import disassemble_hex
from slither.core.cfg.node import NodeType as SlitherNodeType
from slither.slither import Slither
from solc_select import solc_select

import utils
from arg_parser import args
from cfg_traversal_utils import WalkTree
from slither_utils import escape_expression
from utils import disabled_stdout, class_property

PRAGMA_SOLIDITY_VERSION_REGEX = re.compile(r'^pragma\ssolidity\s\^([\d.]+);$')

END_LINE = '\n'


class SolcSelectHelper:
    @class_property
    def versions(self) -> list:
        return solc_select.installed_versions()

    @class_property
    def current_version(self) -> str:
        return solc_select.current_version()[0]

    @class_property
    def available_versions(self) -> list:
        # noinspection PyBroadException
        try:
            return list(solc_select.get_available_versions().keys())
        except Exception:
            return []

    @staticmethod
    def install(version: str) -> bool:
        if version in SolcSelectHelper.versions:
            return True
        with disabled_stdout():
            try:
                solc_select.install_artifacts([version, ])
                return True
            except:
                return False

    @staticmethod
    def select(version: str, install: bool = False) -> bool:
        if version not in SolcSelectHelper.versions:
            if install is False:
                return False
            elif version not in SolcSelectHelper.available_versions:
                return False
            else:
                if SolcSelectHelper.install(version) is False:
                    return False

        with disabled_stdout():
            try:
                solc_select.switch_global_version(version)
                return True
            except:
                return False


class SolcHelper:
    @class_property
    def output_values(self):
        return ["abi", "bin-runtime", "ast", "opcodes", "storage-layout", "metadata", "srcmap", "asm"]

    @staticmethod
    def compile_source(source: str) -> dict:
        return solcx.compile_source(
            source,
            output_values=SolcHelper.output_values
        )

    @staticmethod
    def compile_file(files: Union[str, list]) -> Union[dict, List]:
        result = solcx.compile_files(
            files,
            output_values=SolcHelper.output_values
        )

        if len(result.keys()) == 1:
            return result[next(iter(result))]  # returns the first
        return [{'contract': k, 'compiled': v} for k, v in result.items()]


class SolFile:
    def __init__(self, path):
        self.path = path
        self.cfg_strategy = args.cfg_strategy
        self.target = None

    @cached_property
    def compiler_version(self) -> str:
        with open(self.path) as f:
            for line in f:
                if matched := PRAGMA_SOLIDITY_VERSION_REGEX.match(line):
                    utils.log(f"compiling with solidity compiler version {matched.groups()[0]}")
                    return matched.groups()[0]

    @cached_property
    def source(self) -> str:
        utils.log(f"Path: {self.path}")
        with open(self.path) as f:
            return ''.join(f.readlines())

    @cached_property
    def loc(self) -> int:
        val = 0
        for line in self.source.split('\n'):
            if line.strip() != '' and not line.startswith('//') and not line.startswith('/*'):
                val += 1
        utils.log(f"LoC: {val}")
        return val

    @cached_property
    def compiled(self) -> dict:
        if self.compiler_version:  # TODO otherwise?
            SolcSelectHelper.select(self.compiler_version, install=True)

        compiled = SolcHelper.compile_file(self.path)  # TODO what if there is more than one contract
        if isinstance(compiled, list):
            for contract in compiled:
                if self.slither.contracts[-1].name in contract['contract']:  # The Main Contract
                    return contract['compiled']  # TODO: Maybe all
        else:
            return compiled

    def __get_compiled_param(self, param_name: str) -> Union[str, dict]:
        return self.compiled[param_name]

    @cached_property
    def bin(self) -> str:
        return self.__get_compiled_param('bin-runtime')

    @cached_property
    def bin_cfg(self) -> EVMCFG:
        return EVMCFG(self.bin)

    @cached_property
    def abi(self) -> dict:
        return self.__get_compiled_param('abi')

    @cached_property
    def ast(self) -> dict:
        return self.__get_compiled_param('ast')

    @cached_property
    def opcodes(self) -> str:
        return self.__get_compiled_param('opcodes')

    @cached_property
    def opcodes_pyevmasm(self) -> list:
        return disassemble_hex(self.bin).split('\n')

    @cached_property
    def storage_layout(self) -> dict:
        return self.__get_compiled_param('storage-layout')

    @cached_property
    def metadata(self) -> dict:
        return json.loads(self.__get_compiled_param('metadata'))

    @cached_property
    def srcmap(self) -> dict:
        return self.__get_compiled_param('srcmap')

    @cached_property
    def asm(self) -> dict:
        return self.__get_compiled_param('asm')

    @cached_property
    def slither(self) -> Slither:
        return Slither(self.path)

    @cached_property
    def variables(self):
        # TODO support more contracts

        # First, add global variables
        result = {k: str(v.type) for k, v in self.slither.contracts[-1].variables_as_dict.items()}

        # Second, add function variables
        for func in self.slither.contracts[-1].functions:
            result = result | {k: str(v.type) for k, v in func.variables_as_dict.items()}

        return result

    @cached_property
    def insource_target_annotation(self):
        """
        Find the target with @target annotation in the source code
        :return: (lineno, target line) Tuple.
        """
        for indx, line in enumerate(self.source.split('\n')):
            if "@target" in line:
                return indx + 1, line
        return -1, None

    @cached_property
    def insource_heuristic_annotation(self):
        """
        Find the heuristic based on the @heuristic annotation
        :return: (lineno, the heuristic) Tuple
        """
        for indx, line in enumerate(self.source.split('\n')):
            if "@heuristic" in line:
                assert len(line.strip().split()) == 3  # // @heuristic <val>
                return indx + 1, line.strip().split()[-1]
        return -1, None

    @staticmethod
    def __process_irs(node):
        return [str(ir) for ir in node.irs]

    def __cfg_add_nodes(self, func, node, cfg_x, node_name_prefix=''):
        expr = {
            'sol': [str(node.expression or ''), ],
            'irs': self.__process_irs(node=node),
            'node_type': node.type.name,
            'state_variables_read': [str(var) for var in node.state_variables_read],
            'state_variables_written': [str(var) for var in node.state_variables_written],
            'func_state_variables_read': [str(var) for var in func.state_variables_read],
            'func_state_variables_written': [str(var) for var in func.state_variables_written],
        }
        if node.type.name == "ENTRYPOINT":
            expr["params"] = [param.name for param in func.variables if param.name]
            if node_name_prefix == '':  # TODO: Maybe better implementation on not initializing library_calls
                expr["irs"] = [f"INITIALIZE_FUNC_PARAMS {param_name}" for param_name in expr["params"]]

        # Checks if this node is the target of Targeted Backward Symbolic Execution
        if args.target is not None:
            is_target = \
                node.expression is not None \
                and args.target in node.source_mapping['lines']
        else:  # Read @target annotation if no --target is specified
            lineno, _ = self.insource_target_annotation
            is_target = \
                lineno != -1 \
                and node.expression is not None \
                and lineno in node.source_mapping['lines']
        is_target = is_target or False  # Set False if this is None

        cfg_x.add_node(
            f"{node_name_prefix}{func.name}_{node.node_id}",
            label=f"{func.name}_{node.node_id}{'*' if is_target else ''}|node_type = {node.type}\n\nEXPRESSION:"
                  f" {escape_expression(END_LINE.join(expr[args.cfg_expr_type]))}",
            shape="record",
            lines=node.source_mapping['lines'],
            is_target=is_target,
            **expr,
        )

        if is_target is True:
            self.target = f"{func.name}_{node.node_id}"  # TODO: is it possible to have multiple targets?
            utils.log(f"target node is {self.target}")

        if self.cfg_strategy == 'compound':
            if func.name == 'slitherConstructorVariables' or func.name.startswith("constructor"):
                if node.node_id == 0:
                    cfg_x.add_edge(
                        u_for_edge='START_NODE',
                        v_for_edge=f'{func.name}_0',
                    )
                elif node.node_id == len(func.nodes) - 1 and node_name_prefix == '':
                    cfg_x.add_edge(
                        u_for_edge=f'{func.name}_{node.node_id}',
                        v_for_edge='AFTER_CREATION'
                    )
            elif node.type.name == 'ENTRYPOINT' and node_name_prefix == '':
                cfg_x.add_edge(
                    u_for_edge='AFTER_CREATION',
                    v_for_edge=f'{func.name}_{node.node_id}',
                )

    def __cfg_add_func_edges(self, func, cfg_x, node_name_prefix=''):
        for node in func.nodes:
            if node.type in [SlitherNodeType.IF, SlitherNodeType.IFLOOP]:
                if node.son_true:
                    cfg_x.add_edge(
                        u_for_edge=f"{node_name_prefix}{func.name}_{node.node_id}",
                        v_for_edge=f"{node_name_prefix}{func.name}_{node.son_true.node_id}",
                        label="True"
                    )
                if node.son_false:
                    cfg_x.add_edge(
                        u_for_edge=f"{node_name_prefix}{func.name}_{node.node_id}",
                        v_for_edge=f"{node_name_prefix}{func.name}_{node.son_false.node_id}",
                        label="False"
                    )
            else:
                if node.sons:
                    for son in node.sons:
                        cfg_x.add_edge(
                            u_for_edge=f"{node_name_prefix}{func.name}_{node.node_id}",
                            v_for_edge=f"{node_name_prefix}{func.name}_{son.node_id}",
                        )
                elif self.cfg_strategy == 'compound' and node_name_prefix == '':
                    cfg_x.add_edge(
                        u_for_edge=f"{node_name_prefix}{func.name}_{node.node_id}",
                        v_for_edge="AFTER_TX",
                    )

    def __cfg_process_internal_calls(self, cfg_x):
        for node, irs in nx.get_node_attributes(cfg_x, 'irs').items():
            try:
                matched = next((indx, ir) for indx, ir in enumerate(irs) if 'INTERNAL_CALL,' in ir)
            except StopIteration:
                matched = None

            if matched is not None:
                indx, ir = matched
                prev_irs, next_irs = irs[:indx], irs[indx + 1:]

                if '=' in ir:
                    lvalue, rvalue = ir.split(' = ')
                else:
                    lvalue, rvalue = None, ir
                func_name = re.match(r'^INTERNAL_CALL,\s([\w.]+)\(', rvalue).groups()[0]
                slither_func = next(
                    item for item in self.slither.contracts[-1].functions if
                    item.canonical_name.startswith(func_name))

                # Set parameters
                passed_params_str = rvalue.split(')(')[-1][:-1]
                passed_params = passed_params_str.split(',') if passed_params_str else []
                for passed_param, func_param in zip(passed_params, slither_func.parameters):
                    prev_irs.append(f'{func_param}({func_param.type}) := {passed_param}({func_param.type})')

                # Add nodes and edges for private function
                cfg_x.add_node(f"{node}_before_call", label=f"{node}_before_call", irs=prev_irs)
                prev_node, _ = list(cfg_x.in_edges(node))[0]  # TODO: if more than one in-edge
                edge_data = cfg_x.get_edge_data(prev_node, node).copy()
                cfg_x.remove_edge(prev_node, node)
                if edge_data[0]:
                    cfg_x.add_edge(prev_node, f"{node}_before_call", **edge_data[0])
                else:
                    cfg_x.add_edge(prev_node, f"{node}_before_call")
                for n in slither_func.nodes:
                    self.__cfg_add_nodes(slither_func, n, cfg_x, node_name_prefix=f'{node}_')

                    if n.type.name == 'ENTRYPOINT':
                        cfg_x.add_edge(f"{node}_before_call", f"{node}_{slither_func.name}_{n.node_id}")
                    elif n.type.name == 'RETURN':
                        cfg_x.add_edge(f"{node}_{slither_func.name}_{n.node_id}", node)

                        if lvalue is not None:
                            if str(n.expression).split().__len__() == 1:
                                return_ir = f"{lvalue} := {n.expression}({lvalue.split('(')[1]}"
                            else:
                                return_ir = f"{lvalue} = {n.expression}"
                            next_irs.insert(0, return_ir)

                self.__cfg_add_func_edges(slither_func, cfg_x, node_name_prefix=f'{node}_')

                cfg_x.nodes[node]['irs'] = next_irs

    def __cfg_process_library_calls(self, cfg_x):
        for node, irs in nx.get_node_attributes(cfg_x, 'irs').items():
            try:
                matched = next((indx, ir) for indx, ir in enumerate(irs) if 'LIBRARY_CALL,' in ir)
            except StopIteration:
                matched = None

            if matched is not None:
                indx, ir = matched
                prev_irs, next_irs = irs[:indx], irs[indx + 1:]

                if '=' in ir:
                    lvalue, rvalue = ir.split(' = ')
                else:
                    lvalue, rvalue = None, ir
                _, library_name, func_name = re.match(r'^LIBRARY_CALL,\s([\w.:]+),\sfunction:(\w+).(\w+)\(',
                                                      rvalue).groups()
                slither_library = next(item for item in self.slither.contracts if item.name == library_name)
                slither_func = next(
                    item for item in slither_library.functions if item.name == func_name)

                # Set parameters
                passed_params_str = rvalue.split('arguments:[')[1].strip()[:-1].replace('\'', '')
                passed_params = passed_params_str.split(',') if passed_params_str else []
                for passed_param, func_param in zip(passed_params, slither_func.parameters):
                    prev_irs.append(f'{func_param}({func_param.type}) := {passed_param}({func_param.type})')

                # Add nodes and edges for private function
                cfg_x.add_node(f"{node}_before_call", label=f"{node}_before_call", irs=prev_irs)
                prev_node, _ = list(cfg_x.in_edges(node))[0]  # TODO: if more than one in-edge
                edge_data = cfg_x.get_edge_data(prev_node, node).copy()
                cfg_x.remove_edge(prev_node, node)
                if edge_data[0]:
                    cfg_x.add_edge(prev_node, f"{node}_before_call", **edge_data[0])
                else:
                    cfg_x.add_edge(prev_node, f"{node}_before_call")
                for n in slither_func.nodes:
                    self.__cfg_add_nodes(slither_func, n, cfg_x, node_name_prefix=f'{node}_')

                    if n.type.name == 'ENTRYPOINT':
                        cfg_x.add_edge(f"{node}_before_call", f"{node}_{slither_func.name}_{n.node_id}")
                    elif n.type.name == 'RETURN':
                        cfg_x.add_edge(f"{node}_{slither_func.name}_{n.node_id}", node)

                        if lvalue is not None:
                            if str(n.expression).split().__len__() == 1:
                                return_ir = f"{lvalue} := {n.expression}({lvalue.split('(')[1]}"
                            else:
                                return_ir = f"{lvalue} = {n.expression}"
                            next_irs.insert(0, return_ir)

                self.__cfg_add_func_edges(slither_func, cfg_x, node_name_prefix=f'{node}_')

                cfg_x.nodes[node]['irs'] = next_irs

    @cached_property
    def cfg(self) -> nx.MultiDiGraph:
        cfg_x = nx.MultiDiGraph()

        if self.cfg_strategy == 'compound':
            utils.log("compound mode activated.")

            cfg_x.add_node("START_NODE", label=f"start", irs=["INITIALIZE_GLOBS", ])
            cfg_x.add_node("END_NODE", label="end")
            cfg_x.add_node("AFTER_CREATION", label="after constructor", irs=['TRANSACTION_STARTS', ])
            cfg_x.add_node("AFTER_TX", label="after transaction")

            cfg_x.add_edge("AFTER_TX", "END_NODE")
            cfg_x.add_edge("AFTER_TX", "AFTER_CREATION")

        utils.log(f"Contract Name: {self.slither.contracts[-1].name}")
        for func in self.slither.contracts[-1].functions:  # TODO Support more contracts
            if func.visibility in ['private', 'internal'] and not (
                    func.name == 'slitherConstructorVariables' or func.name.startswith("constructor")):
                continue

            # Traverse all nodes and add to networkx version
            for node in func.nodes:
                self.__cfg_add_nodes(func=func, node=node, cfg_x=cfg_x)

            # Add edges
            self.__cfg_add_func_edges(func=func, cfg_x=cfg_x)

        # noinspection PyArgumentList
        if not cfg_x.out_edges("START_NODE"):
            cfg_x.add_edge(
                u_for_edge='START_NODE',
                v_for_edge='AFTER_CREATION'
            )

        self.__cfg_process_internal_calls(cfg_x)
        self.__cfg_process_library_calls(cfg_x)

        utils.log(f"#NUM_OF_CFG_NODES: {cfg_x.nodes.__len__()}", level='debug')
        return cfg_x

    @cached_property
    def reversed_cfg(self) -> nx.MultiDiGraph:
        return self.cfg.reverse(copy=True)

    @cached_property
    def find_test_data(self):
        utils.log(f"finding optimal SAT path from '{self.target}' to 'start'", level='debug')
        return WalkTree(contract=self, reversed_cfg=self.reversed_cfg, target_node=self.target).traverse()
