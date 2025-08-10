#!/bin/bash

PROJECT_DIR="xp"

BINARIES=("riblt" "rbf_riblt" "bf_riblt")

# Test generation parameters
NR_TESTS=30
NR_ELEMENTS_TO_GENERATE=200000
SET_CARDINALITY=100000
TEST_DATA_DIR="./test_data"
RESULTS_DIR="./results"
TEST_DIFFS=(10 20 30 60 100 200 400 700 1000 1400 2500 4000 8000 10000 16000 30000 50000 100000)

rm -rf "$RESULTS_DIR"
mkdir -p "$RESULTS_DIR"

# Step 1: Ensure test data exists.
# Check if the output directory exists and contains the expected number of files.
echo "--- Checking for test data ---"
if [ ! -d "$TEST_DATA_DIR" ] || [ $(ls "$TEST_DATA_DIR" | wc -l) -lt "$NR_TESTS" ]; then
    echo "Test data not found or incomplete. Generating new sets..."
    
    # Build the set_generator binary first
    cd "$PROJECT_DIR" || exit
    cargo build --release --bin set_generator
    cd ..

    # Run the set_generator to create the data
    ./"$PROJECT_DIR"/target/release/set_generator --nr-tests "$NR_TESTS" --nr-elements "$NR_ELEMENTS_TO_GENERATE" --output-dir "$TEST_DATA_DIR"
else
    echo "Test data already exists and is complete. Skipping generation."
fi

# Step 2: Build all executables.
# Cargo will only re-compile binaries that have changed, so we can build them all.
echo "--- Building all binaries ---"

cd "$PROJECT_DIR" || exit
cargo build --release
cd ..

# Step 3: Run tests for each binary.
echo "--- Running all tests ---"
# Create the results directory if it doesn't exist
mkdir -p test_results


binary="riblt"
echo "--- Running tests for: $binary ---"
for d in "${TEST_DIFFS[@]}"; do
    echo "--- Running tests for d = $d ---"
    for i in $(seq 0 $((NR_TESTS - 1))); do
		./"$PROJECT_DIR"/target/release/$binary $TEST_DATA_DIR $i $SET_CARDINALITY $d $RESULTS_DIR
    done
done

binary="bf_riblt"
echo "--- Running tests for: $binary ---"
for fpr in 0.01 0.1 0.25; do
	echo "--- Running tests for fpr = $fpr ---"
	for d in "${TEST_DIFFS[@]}"; do
		echo "--- Running tests for d = $d ---"
		for i in $(seq 0 $((NR_TESTS - 1))); do
			./"$PROJECT_DIR"/target/release/$binary $TEST_DATA_DIR $i $SET_CARDINALITY $d $RESULTS_DIR $fpr
		done
	done
done

binary="rbf_riblt"
echo "--- Running tests for: $binary ---"
for d in "${TEST_DIFFS[@]}"; do
    echo "--- Running tests for d = $d ---"
    for i in $(seq 0 $((NR_TESTS - 1))); do
		./"$PROJECT_DIR"/target/release/$binary $TEST_DATA_DIR $i $SET_CARDINALITY $d $RESULTS_DIR
    done
done

echo "--- All tests finished ---"
echo "Results are available in $PROJECT_DIR/test_results"