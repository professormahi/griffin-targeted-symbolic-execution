from exporters import export_requested_parameters
from sol_utils import SolFile
from workspace import workspace

if __name__ == '__main__':
    contract = SolFile(f"{workspace}/source.sol")

    export_requested_parameters(contract)

    cfg_path = contract.find_test_data
    if cfg_path is None:
        print("No path found from target to smart contract entrypoint")
    else:
        print(f"Sat inputs: {cfg_path.sat_inputs}")
