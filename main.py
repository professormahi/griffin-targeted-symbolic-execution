from datetime import datetime

from exporters import export_requested_parameters
from sol_utils import SolFile
from utils import log
from workspace import workspace

if __name__ == '__main__':
    contract = SolFile(f"{workspace}/source.sol")

    export_requested_parameters(contract)

    start_time = datetime.utcnow().timestamp()
    cfg_path = contract.find_test_data
    if cfg_path is None:
        print("No path found from target to smart contract entrypoint")
    else:
        print(f"Sat inputs: {cfg_path.sat_inputs}")
    exec_time = datetime.utcnow().timestamp() - start_time
    log(f"Exec Time: {exec_time:.2}s", level="info")
