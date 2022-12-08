import argparse
from functools import partial
from typing import Any


def add_boolean(self, arg_name: str, dest: str, default: Any, **extra):
    if arg_name.startswith('--'):
        arg_name = arg_name.replace('--', '')

    self.add_argument(f"--{arg_name}", dest=dest, action='store_true', **extra)
    self.add_argument(f"--no-{arg_name}", dest=dest, action='store_false', **extra)
    self.set_defaults(**{dest: default})


parser = argparse.ArgumentParser(description='')
parser.add_boolean = partial(add_boolean, parser)

parser.add_argument("contract", help="The smart contract solidity file to process")

parser.add_argument('--debug', dest="debug", action='store_true', help='Debug Mode', default=False)
parser.add_boolean('--clean', dest='clean_workspace', default=False,
                   help="Cleans the output/ directory before adding new workspace directories.")

# Targeted Backward Symbolic Execution
parser.add_argument('--target', dest='target', type=int, required=False,
                    help="The line-number which the target of Targeted Backward Symbolic Execution")

# CFG Options
parser.add_argument('--cfg-strategy', dest='cfg_strategy', default='',
                    help="The CFG drawing strategy. Choose compound for compounding all functions.")
parser.add_argument('--cfg-expr-type', dest='cfg_expr_type', default='sol', choices=['sol', 'irs', 'irs_ssa'],
                    help="The expressions' type for CFG. Available options are 'sol' for solidity expressions, "
                         "'irs' for IR expressions, and 'irs_ssa' for SSA IRs.")

# Heuristics
parser.add_argument('--heuristic', dest='heuristic', default='floyd_warshall',
                    help="The heuristic to traverse CFG and find test data.")

# Exporters
parser.add_boolean('--export-ast', dest='export_ast', default=True,
                   help="Store the ast value of the smart contract in output directory as `output.ast`.")
parser.add_boolean('--export-bin', dest='export_bin', default=True,
                   help="Store the bin(evm) value of the smart contract in output directory as `output.bin`.")
parser.add_boolean('--export-abi', dest='export_abi', default=True,
                   help="Store the ABI value of the smart contract in output directory as `output.abi`.")
parser.add_boolean('--export-opcodes', dest='export_opcodes', default=True,
                   help="Store the OPCodes of the smart contract in output directory as `output.opcodes`.")
parser.add_boolean('--export-opcodes-pyevmasm', dest='export_opcodes_pyevmasm', default=True,
                   help="Store the converted opcodes by pyevmasm of the smart contract in output directory as "
                        "`output.opcodes_pyevmasm`.")
parser.add_boolean('--export-storage-layout', dest='export_storage_layout', default=True,
                   help="Store the storage-layout of the contract in output directory as `output.storage_layout`.")
parser.add_boolean('--export-metadata', dest='export_metadata', default=True,
                   help="Store the metadata for the smart contract in output directory as `output.metadata`.")
parser.add_boolean('--export-srcmap', dest='export_srcmap', default=True,
                   help="Store the srcmap for the smart contract in output directory as `output.srcmap`.")
parser.add_boolean('--export-asm', dest='export_asm', default=True,
                   help="Store the ASM for the smart contract in output directory as `output.asm`.")
parser.add_boolean('--export-cfg', dest='export_cfg__dot', default=True,
                   help="Store the CFG for the smart contract in output directory as `cfg.dot`.")
parser.add_boolean('--export-reverse-cfg', dest='export_reversed_cfg__dot', default=True,
                   help="Store the Reversed-CFG for the smart contract in output directory as `reversed_cfg.dot`.")

args = parser.parse_args()
