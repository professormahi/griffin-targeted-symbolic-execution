#! /bin/bash

# Number of Runs
NUM_RUNS="${NUM_RUNS:-1}"

# Check if in correct dir
current_dir=$(basename "$PWD")
if [ "$current_dir" != "smart_contract_testing" ]; then
  echo "Wrong directory"
  exit 1
fi

source .env/bin/activate || exit 1

# Remove previous results
rm output/* -rf || exit 1

# Start testing
for i in $(seq 1 $NUM_RUNS); do
  for j in $(seq 1 8); do
      cat << HERE  > /tmp/multi_tx_$j.sol
pragma solidity ^0.8.0;

contract multi_tx_$j {
    uint public counter = 0;
    uint public maximum_bid = 0;
    uint private threshold = $j;

    function bid(uint value) public {
        counter += 1;
        if (value > maximum_bid)
            maximum_bid = value;
    }

    function check() public returns (uint) {
        if (counter == threshold)
            return maximum_bid;  // @target maximum_bid > 100
        return 0;
    }
}
HERE

    echo "running multi_tx_$j.sol"
    python main.py /tmp/multi_tx_$j.sol > /dev/null

    echo "running multi_tx_$j.sol [state_variables_based]"
    python main.py /tmp/multi_tx_$j.sol --heuristic state_variables_based > /dev/null


  done
done