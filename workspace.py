import pathlib
import re
import shutil
from datetime import datetime
from pathlib import Path

from arg_parser import args
from utils import log

OUTPUT_DIR = pathlib.Path('output/')


def copy_contract_to_workspace(_workspace):
    if args.target is not None:  # We have --target command
        shutil.copy(args.contract, f"{_workspace}/source.sol")
    else:  # @target annotation exists
        # Convert @target annotation if it has condition
        with open(args.contract, 'r') as contract_file, open(f"{_workspace}/source.sol", "w") as temp_file:
            for line in contract_file.readlines():
                temp_file.write(re.sub(
                    r'(?P<statement>.+)//\s+@target\s+(?P<cond>.+)$',
                    r'{if(\g<cond>){\n assert(true); // @target\n}\n\g<statement>}\n',
                    line
                ))


def prepare_workspace() -> Path:
    if args.clean_workspace:
        log('cleaning workspace...', level='debug')
        shutil.rmtree(OUTPUT_DIR.__str__())
        OUTPUT_DIR.mkdir()

    log('creating temp directory...', level='debug')
    tempdir = OUTPUT_DIR.joinpath(datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
    __workspace = pathlib.Path(tempdir)
    __workspace.mkdir()

    copy_contract_to_workspace(__workspace)

    return __workspace


workspace = prepare_workspace()
