import json
import re
from functools import cached_property
from typing import Union

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
        return list(solc_select.get_available_versions().keys())

    @staticmethod
    def install(version: str) -> bool:
        with disabled_stdout():
            try:
                solc_select.install_artifacts([version, ])
                return True
            except:
                return False

    @staticmethod
    def select(version: str, install: bool = False) -> bool:
        if version not in SolcSelectHelper.available_versions:
            return False
        if version not in SolcSelectHelper.versions:
            if install is False:
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
    def compile_file(files: Union[str, list]) -> dict:
        result = solcx.compile_files(
            files,
            output_values=SolcHelper.output_values
        )

        if len(result.keys()) == 1:
            return result[next(iter(result))]  # returns the first
        return result


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
        with open(self.path) as f:
            return ''.join(f.readlines())

    @cached_property
    def compiled(self) -> dict:
        if self.compiler_version:  # TODO otherwise?
            SolcSelectHelper.select(self.compiler_version, install=True)

        return SolcHelper.compile_file(self.path)  # TODO what if there is more than one contract

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
        result = {k: str(v.type) for k, v in self.slither.contracts[0].variables_as_dict.items()}

        # Second, add function variables
        for func in self.slither.contracts[0].functions:
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
                return indx, line
        return -1, None

    @cached_property
    def cfg(self) -> nx.MultiDiGraph:
        cfg_x = nx.MultiDiGraph()

        if self.cfg_strategy == 'compound':
            utils.log("compound mode activated.")

            cfg_x.add_node("START_NODE", label=f"start", irs=["INITIALIZE_GLOBS", ])
            cfg_x.add_node("END_NODE", label="end")
            cfg_x.add_node("AFTER_CREATION", label="after constructor")
            cfg_x.add_node("AFTER_TX", label="after transaction")

            cfg_x.add_edge("AFTER_TX", "END_NODE")
            cfg_x.add_edge("AFTER_TX", "AFTER_CREATION")

        for func in self.slither.contracts[0].functions:  # TODO Support more contracts
            # Traverse all nodes and add to networkx version
            for node in func.nodes:
                expr = {
                    'sol': [str(node.expression or ''), ],
                    'irs': [str(ir) for ir in node.irs],
                    'irs_ssa': [str(ir) for ir in node.irs_ssa],
                }

                # Checks if this node is the target of Targeted Backward Symbolic Execution
                if args.target is not None:
                    is_target = \
                        node.expression is not None \
                        and args.target in node.source_mapping.lines
                else:  # Read @target annotation if no --target is specified
                    lineno, _ = self.insource_target_annotation
                    is_target = \
                        lineno != -1 \
                        and node.expression is not None \
                        and lineno in node.source_mapping.lines
                is_target = is_target or False  # Set False if this is None

                cfg_x.add_node(
                    f"{func.name}_{node.node_id}",
                    label=f"{func.name}_{node.node_id}{'*' if is_target else ''}|node_type = {node.type}\n\nEXPRESSION:"
                          f" {escape_expression(END_LINE.join(expr[args.cfg_expr_type]))}",
                    shape="record",
                    lines=node.source_mapping.lines,
                    is_target=is_target,
                    **expr,
                )

                if is_target is True:
                    self.target = f"{func.name}_{node.node_id}"  # TODO: is it possible to have multiple targets?
                    utils.log(f"target node is {self.target}")

                if self.cfg_strategy == 'compound':
                    if func.name == 'slitherConstructorVariables' or func.name.startswith("constructor"):
                        cfg_x.add_edge(
                            u_for_edge='START_NODE',
                            v_for_edge=f'{func.name}_{node.node_id}',
                        )
                        cfg_x.add_edge(
                            u_for_edge=f'{func.name}_{node.node_id}',
                            v_for_edge='AFTER_CREATION'
                        )
                    elif node.type.name == 'ENTRYPOINT':
                        cfg_x.add_edge(
                            u_for_edge='AFTER_CREATION',
                            v_for_edge=f'{func.name}_{node.node_id}',
                        )

            # Add edges
            for node in func.nodes:
                if node.type in [SlitherNodeType.IF, SlitherNodeType.IFLOOP]:
                    if node.son_true:
                        cfg_x.add_edge(
                            u_for_edge=f"{func.name}_{node.node_id}",
                            v_for_edge=f"{func.name}_{node.son_true.node_id}",
                            label="True"
                        )
                    if node.son_false:
                        cfg_x.add_edge(
                            u_for_edge=f"{func.name}_{node.node_id}",
                            v_for_edge=f"{func.name}_{node.son_false.node_id}",
                            label="False"
                        )
                else:
                    if node.sons:
                        for son in node.sons:
                            cfg_x.add_edge(
                                u_for_edge=f"{func.name}_{node.node_id}",
                                v_for_edge=f"{func.name}_{son.node_id}",
                            )
                    elif self.cfg_strategy == 'compound':
                        cfg_x.add_edge(
                            u_for_edge=f"{func.name}_{node.node_id}",
                            v_for_edge="AFTER_TX",
                        )

        # noinspection PyArgumentList
        if not cfg_x.out_edges("START_NODE"):
            cfg_x.add_edge(
                u_for_edge='START_NODE',
                v_for_edge='AFTER_CREATION'
            )
        return cfg_x

    @cached_property
    def reversed_cfg(self) -> nx.MultiDiGraph:
        return self.cfg.reverse(copy=True)

    @cached_property
    def find_test_data(self):
        utils.log(f"finding optimal SAT path from '{self.target}' to 'start'", level='debug')
        return WalkTree(contract=self, reversed_cfg=self.reversed_cfg, target_node=self.target).traverse()
