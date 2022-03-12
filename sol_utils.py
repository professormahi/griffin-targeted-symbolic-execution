import json
import re
from functools import cached_property
from typing import Union

import solcx
from evm_cfg_builder import CFG as EVMCFG
from pyevmasm import disassemble_hex
from slither.core.cfg.node import NodeType as SlitherNodeType
from slither.slither import Slither
from solc_select import solc_select
import networkx as nx

from slither_utils import escape_expression
from utils import disabled_stdout, class_property

PRAGMA_SOLIDITY_VERSION_REGEX = re.compile(r'^pragma\ssolidity\s\^([\d.]+);$')


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

    @cached_property
    def compiler_version(self) -> str:
        with open(self.path) as f:
            for line in f:
                if matched := PRAGMA_SOLIDITY_VERSION_REGEX.match(line):
                    return matched.groups()[0]

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
    def cfg(self) -> nx.MultiDiGraph:
        cfg_x = nx.MultiDiGraph()

        for func in self.slither.contracts[0].functions:  # TODO Support more contracts
            # Traverse all nodes and add to networkx version
            for node in func.nodes:
                cfg_x.add_node(
                    f"{func.name}_{node.node_id}",
                    label=f"{func.name}_{node.node_id}|node_type = {node.type}\n\nexpression ="
                          f" {escape_expression(node.expression)}",
                    shape="record"
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
                    for son in node.sons:
                        cfg_x.add_edge(
                            u_for_edge=f"{func.name}_{node.node_id}",
                            v_for_edge=f"{func.name}_{son.node_id}",
                        )

        return cfg_x
