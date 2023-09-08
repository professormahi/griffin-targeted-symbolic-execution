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
contracts=$(find sample-smart-contracts/ -iname "*.sol" -type f)
for i in $(seq 1 $NUM_RUNS); do
  for item in $contracts; do
    expected_result=$(grep "@result" "$item" | cut -d" " -f3-)

    if [ "$expected_result" != "" ]; then
      echo "running $item"

      # Creating temp files
      time_stamp=$(date '+%s')
      sol_file_name=$(basename "item")
      expected_file=/tmp/smart_contract_testing-"$sol_file_name"-"$time_stamp".expected
      output_file=/tmp/smart_contract_testing-"$sol_file_name"-"$time_stamp".out

      # Running
      python main.py "$item" > "$output_file"

      # Comparing the results
      echo "$expected_result" > "$expected_file"
      diff -u --color "$expected_file" "$output_file"

      # Cleaning
      rm "$expected_file" "$output_file"
    fi
  done
done