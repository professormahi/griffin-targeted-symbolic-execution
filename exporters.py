import json
from typing import Any, Union, List

import networkx as nx

from arg_parser import args
from utils import log
from workspace import workspace


class Exporter:
    @staticmethod
    def export(value_to_export: Any) -> str:
        return getattr(
            Exporter,
            f'_export_{type(value_to_export).__name__}',
            lambda x: str(x)
        )(value_to_export)

    @staticmethod
    def _export_dict(value_to_export: Union[dict, List[dict]]) -> str:
        return json.dumps(value_to_export, indent=2)

    @staticmethod
    def _export_list(value_to_export: list) -> str:
        if isinstance(value_to_export[0], dict):
            return Exporter._export_dict(value_to_export)

        return '\n'.join([Exporter.export(item) for item in value_to_export])

    # noinspection PyPep8Naming
    @staticmethod
    def _export_MultiDiGraph(value_to_export: nx.MultiDiGraph) -> str:
        return nx.nx_pydot.to_pydot(value_to_export)


def export_requested_parameters(contract):
    log("start exporting requested parameters...")

    requested_export_list = filter(lambda x: x.startswith('export_'), args.__dict__.keys())
    for item in requested_export_list:
        if getattr(args, item, False) is True:
            key_to_export = item.replace('export_', '')
            if "__" in item:  # Means for export_key__format we should change naming format to key.format
                key_to_export = key_to_export.split("__")[0]
                file_to_open = f"{workspace}/{key_to_export}.{item.split('__')[1]}"
            else:
                file_to_open = f"{workspace}/output.{key_to_export}"

            value_to_export = Exporter.export(getattr(contract, key_to_export))

            with open(file_to_open, "w") as f:
                f.write(value_to_export.__str__())
