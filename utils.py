import os
import sys

from workspace import workspace


class disabled_stdout:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


# noinspection PyPep8Naming
class class_property(property):
    # noinspection PyMethodOverriding
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


def log(msg: str, level='info') -> None:
    from arg_parser import args

    if args.debug:
        print(f'[{level}] {msg}', file=sys.stderr)

    with open(f"{workspace}/out.log", "a") as f:
        print(f'[{level}] {msg}', file=f)
