from arg_parser import args
from exporters import export_requested_parameters
from sol_utils import SolFile

if __name__ == '__main__':
    contract = SolFile(args.contract)

    export_requested_parameters(contract)
