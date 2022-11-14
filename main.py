from arg_parser import args
from exporters import export_requested_parameters
from sol_utils import SolFile

if __name__ == '__main__':
    contract = SolFile(args.contract)

    export_requested_parameters(contract)

    cfg_path = contract.find_test_data
    if cfg_path is None:
        print("No path found from target to smart contract entrypoint")
    else:
        print(f"Sat inputs: {cfg_path.sat_inputs}")
