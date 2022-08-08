from arg_parser import args
from cfg_traversal_utils import CFGPath
from exporters import export_requested_parameters
from sol_utils import SolFile

if __name__ == '__main__':
    contract = SolFile(args.contract)

    export_requested_parameters(contract)

    for path in contract.shortest_path:  # TODO remove and better results
        cfg_path = CFGPath(contract.reversed_cfg, *path)
        for i in range(len(cfg_path.expressions)):
            print(cfg_path.expressions[i], cfg_path.constrains[i])
