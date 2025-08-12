#!/usr/bin/env python3

import os
import subprocess
import shutil

# --- Configuration ---
PROJECT_DIR = "xp"
NR_TESTS = 30
SET_CARDINALITY = 100000
TEST_DATA_DIR = "./test_data"
RESULTS_DIR = "./results/30"
TEST_NAME = "similarity"

class Algorithm:
    """Base class for all algorithm test runners."""
    def run(self):
        """Runs the tests for the algorithm over a list of test differences."""
        raise NotImplementedError("Subclasses must implement the run method.")

class RIBLT(Algorithm):
    """Test runner for the RIBLT algorithm."""
    build_dir = os.path.join(PROJECT_DIR, "target", "release")
    binary_name = "riblt"

    def run(self):
        print(f"--- Running tests for: {self.binary_name} ---")
        cmd = [
            os.path.join(self.build_dir, self.binary_name),
            f"{TEST_DATA_DIR}/{TEST_NAME}",
            str(NR_TESTS),
            f"{RESULTS_DIR}/{TEST_NAME}",
        ]
        subprocess.run(cmd, check=True)

class RBF_RIBLT(Algorithm):
    """Test runner for the RBF_RIBLT algorithm."""
    build_dir = os.path.join(PROJECT_DIR, "target", "release")
    binary_name = "rbf_riblt"

    def run(self):
        print(f"--- Running tests for: {self.binary_name} ---")
        cmd = [
            os.path.join(self.build_dir, self.binary_name),
            f"{TEST_DATA_DIR}/{TEST_NAME}",
            str(NR_TESTS),
            f"{RESULTS_DIR}/{TEST_NAME}",
        ]
        subprocess.run(cmd, check=True)
                
class PinSketch(Algorithm):
    """Test runner for the PinSketch algorithm."""
    build_dir = os.path.join(PROJECT_DIR, "target", "release")
    binary_name = "pinsketch"

    def run(self):
        print(f"--- Running tests for: {self.binary_name} ---")
        cmd = [
            os.path.join(self.build_dir, self.binary_name),
            f"{TEST_DATA_DIR}/{TEST_NAME}",
            str(NR_TESTS),
            f"{RESULTS_DIR}/{TEST_NAME}",
        ]
        subprocess.run(cmd, check=True)

class BF_RIBLT(Algorithm):
    """Test runner for the BF_RIBLT algorithm, which includes an FPR value."""
    build_dir = os.path.join(PROJECT_DIR, "target", "release")
    binary_name = "bf_riblt"

    def __init__(self, fpr):
        self.fpr = fpr

    def run(self):
        print(f"--- Running tests for: {self.binary_name} ---")
        cmd = [
            os.path.join(self.build_dir, self.binary_name),
            f"{TEST_DATA_DIR}/{TEST_NAME}",
            str(NR_TESTS),
            f"{RESULTS_DIR}/{TEST_NAME}",
            str(self.fpr)
        ]
        subprocess.run(cmd, check=True)

        
def ensure_test_data_similarity(set_generator_path):
    start_similarity = 0
    end_similarity = 100
    nr_steps = 20
    
    for similarity in range(start_similarity, end_similarity+1, (end_similarity-start_similarity)//nr_steps):
        similarity = similarity / 100        
        #derived such that nr_common/(nr_common+nr_differences) = similarity
        nr_common = (2*similarity*SET_CARDINALITY)/(1 + similarity)
        nr_differences = int((SET_CARDINALITY - nr_common)*2)
        
        current_similarity_test_data_folder = f"{TEST_DATA_DIR}/{TEST_NAME}/d_{nr_differences}"
        
        if not os.path.exists(current_similarity_test_data_folder):
            print(f"Test data not found for similarity={similarity}. Generating...")
            cmd = [
                set_generator_path,
                "--nr-tests", str(NR_TESTS),
                "--set-cardinality", str(SET_CARDINALITY),
                "--nr-differences", str(nr_differences),
                "--output-dir", current_similarity_test_data_folder,
                "--test-type", TEST_NAME
            ]
            subprocess.run(cmd, check=True)

def ensure_test_data():
    """Checks for test data and generates it if it's missing."""
    print("Generating test data.")
    # Build the set_generator binary
    os.chdir(PROJECT_DIR)
    subprocess.run(["cargo", "build", "--release", "--bin", "set_generator"], check=True)
    os.chdir("..")

    # Run the generator
    set_generator_path = os.path.join(PROJECT_DIR, "target", "release", "set_generator")
    if TEST_NAME=="similarity":
        ensure_test_data_similarity(set_generator_path)
    else:
        raise Exception(f"Test name {TEST_NAME} not supported")


def main():
    """Main function to orchestrate the test run."""
    print("--- Clearing old results and preparing directory ---")
    shutil.rmtree(f"{RESULTS_DIR}/{TEST_NAME}", ignore_errors=True)
    os.makedirs(f"{RESULTS_DIR}/{TEST_NAME}")

    ensure_test_data()

    print("--- Building all binaries ---")
    os.chdir(PROJECT_DIR)
    subprocess.run(["cargo", "build", "--release"], check=True)
    os.chdir("..")

    print("--- Running all tests ---")
    algorithms: list[Algorithm] = [
        RIBLT(),
        BF_RIBLT(0.01),
        BF_RIBLT(0.1),
        BF_RIBLT(0.25),
        RBF_RIBLT(),
        PinSketch()
    ]
    
    for algo in algorithms:
        algo.run()

    print("--- All tests finished ---")
    print(f"Results are available in {RESULTS_DIR}")

if __name__ == "__main__":
    main()
