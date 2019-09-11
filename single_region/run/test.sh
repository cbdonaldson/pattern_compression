## Run this test script to ensure everything is properly set up
##
## Usage: source test.sh <num_components> <max_strip> <max_col>
##
## example: run the following command..
##
## source test.sh 2 21 1

export num_components=$1
export max_strip=$2
export max_col=$3

source pattern_approximation.sh testbank $num_components $max_strip $max_col
python read_pattern_bank.py ../outputs/testbank/bin/compressed_patterns.bin compressed
