import utils
from arg_parser import args
from cfg_traversal_utils import CFGPath
from exporters import export_requested_parameters
from sol_utils import SolFile

if __name__ == '__main__':
    contract = SolFile(args.contract)

    export_requested_parameters(contract)

    for path in contract.shortest_path:  # TODO remove and better results
        cfg_path = CFGPath(contract.reversed_cfg, *path, variables=contract.variables)
        for i in range(len(cfg_path.expressions)):
            utils.log(f"{cfg_path.expressions[i].ljust(50)} {cfg_path.constraints[i]}", level='debug')

        utils.log(f"Is Sat? {cfg_path.is_sat}", level='debug')
        utils.log(f"Sat inputs: {cfg_path.sat_inputs}", level='debug')

        if cfg_path.is_sat:
            break
