import pathlib
import shutil
from datetime import datetime
from pathlib import Path

from arg_parser import args
from utils import log

OUTPUT_DIR = pathlib.Path('output/')


def prepare_workspace() -> Path:
    if args.clean_workspace:
        log('cleaning workspace...')
        shutil.rmtree(OUTPUT_DIR.__str__())
        OUTPUT_DIR.mkdir()

    log('creating temp directory...')
    tempdir = OUTPUT_DIR.joinpath(datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
    __workspace = pathlib.Path(tempdir)
    __workspace.mkdir()

    return __workspace


workspace = prepare_workspace()
