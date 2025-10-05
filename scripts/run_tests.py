#!/usr/bin/env python3

import os
import subprocess
from PBS.parameter_calc import get_best_param, TARGET_SUCCESS_RATE, AVG_DIFF, MAX_ROUND, SPLIT_NUM, INF_RATIO 
import math

# --- Configuration ---
PROJECT_DIR = "xp"
NR_TESTS = 30 #number of trials per measurement
SET_CARDINALITY = 100000
TEST_DATA_DIR = "./test_data"
RESULTS_DIR = "./results"
TEST_NAME = "similarity"

class TowEstimator:
    project_dir = "pbs_organized/estimators"
    binary_name = "tow_estimator"
    
    def build(self):
        os.chdir(self.project_dir)
        subprocess.run(["make"], check=True)
        os.chdir("../..")
    
    def run(self, nr_differences, test):
        cmd = [
            os.path.join(self.project_dir, self.binary_name),
            f"{TEST_DATA_DIR}/{TEST_NAME}/d_{nr_differences}/test_{test}",
        ]
        subprocess.run(cmd, check=True)

class Algorithm:
    """Base class for all algorithm test runners."""
    def run(self):
        """Runs the tests for the algorithm over a list of test differences."""
        raise NotImplementedError("Subclasses must implement the run method.")
    def to_string(self) -> str:
        raise NotImplementedError("Subclasses must implement the to_string method.")
    def build(self):
        """Builds algorithm binary"""
        raise NotImplementedError("Subclasses must implement the build method.")
        

class RIBLT(Algorithm):
    """Test runner for the RIBLT algorithm."""
    build_dir = os.path.join(PROJECT_DIR, "target", "release")
    binary_name = "riblt"

    def run(self):
        print(f"--- Running tests for: {self.to_string()} ---")
        cmd = [
            os.path.join(self.build_dir, self.binary_name),
            f"{TEST_DATA_DIR}/{TEST_NAME}",
            str(NR_TESTS),
            f"{RESULTS_DIR}/{TEST_NAME}",
        ]
        subprocess.run(cmd, check=True)

    def to_string(self) -> str:
        return "Rateless"
    
    def build(self):
        os.chdir(PROJECT_DIR)
        subprocess.run(["cargo", "build", "--release", "--bin", self.binary_name], check=True)
        os.chdir("..")

class RBF_RIBLT_BAYESIAN_COST(Algorithm):
    """Test runner for the RBF_RIBLT algorithm with the Bayesian Cost Stopping Strategy."""
    project_dir = "xp"
    build_dir = os.path.join(project_dir, "target", "release")
    binary_name = "rbf_riblt_bayesian_cost"

    def run(self):
        print(f"--- Running tests for: {self.to_string()} ---")
        cmd = [
            os.path.join(self.build_dir, self.binary_name),
            f"{TEST_DATA_DIR}/{TEST_NAME}",
            str(NR_TESTS),
            f"{RESULTS_DIR}/{TEST_NAME}",
        ]
        subprocess.run(cmd, check=True)

    def to_string(self) -> str:
        return "RBloom+Rateless+BayesianCost[]"
    
    def build(self):
        os.chdir(PROJECT_DIR)
        subprocess.run(["cargo", "build", "--release", "--bin", self.binary_name], check=True)
        os.chdir("..")   
        
class RBF_RIBLT_EXPECTED_COST(Algorithm):
    """Test runner for the RBF_RIBLT algorithm with the Expected Cost Stopping Strategy."""
    project_dir = "xp"
    build_dir = os.path.join(project_dir, "target", "release")
    binary_name = "rbf_riblt_expected_cost"

    def run(self):
        print(f"--- Running tests for: {self.to_string()} ---")
        cmd = [
            os.path.join(self.build_dir, self.binary_name),
            f"{TEST_DATA_DIR}/{TEST_NAME}",
            str(NR_TESTS),
            f"{RESULTS_DIR}/{TEST_NAME}",
        ]
        subprocess.run(cmd, check=True)

    def to_string(self) -> str:
        return "RBloom+Rateless+ExpectedCost[]"
    
    def build(self):
        os.chdir(PROJECT_DIR)
        subprocess.run(["cargo", "build", "--release", "--bin", self.binary_name], check=True)
        os.chdir("..")  
        

class RBF_RIBLT_ANGLE_HEURISTIC(Algorithm):
    """Test runner for the RBF_RIBLT algorithm with the Angle Heuristic Stopping Strategy."""
    project_dir = "xp"
    build_dir = os.path.join(project_dir, "target", "release")
    binary_name = "rbf_riblt_angle_heuristic"

    def __init__(self, angle_threshold_deg):
        self.angle_threshold_deg = angle_threshold_deg

    def run(self):
        print(f"--- Running tests for: {self.to_string()} ---")
        cmd = [
            os.path.join(self.build_dir, self.binary_name),
            f"{TEST_DATA_DIR}/{TEST_NAME}",
            str(NR_TESTS),
            f"{RESULTS_DIR}/{TEST_NAME}",
            str(self.angle_threshold_deg)
        ]
        subprocess.run(cmd, check=True)

    def to_string(self) -> str:
        return f"RBloom+Rateless+AngleHeuristic[angle={self.angle_threshold_deg}]"
    
    def build(self):
        os.chdir(PROJECT_DIR)
        subprocess.run(["cargo", "build", "--release", "--bin", self.binary_name], check=True)
        os.chdir("..")

class RBF_RIBLT_BAYESIAN_SIMILARITY(Algorithm):
    """Test runner for the RBF_RIBLT algorithm with the Bayesian Similarity Stopping Strategy."""
    project_dir = "xp"
    build_dir = os.path.join(project_dir, "target", "release")
    binary_name = "rbf_riblt_bayesian_similarity"

    def __init__(self, target_similarity):
        self.target_similarity = target_similarity

    def run(self):
        print(f"--- Running tests for: {self.to_string()} ---")
        cmd = [
            os.path.join(self.build_dir, self.binary_name),
            f"{TEST_DATA_DIR}/{TEST_NAME}",
            str(NR_TESTS),
            f"{RESULTS_DIR}/{TEST_NAME}",
            str(self.target_similarity)
        ]
        subprocess.run(cmd, check=True)

    def to_string(self) -> str:
        return f"RBloom+Rateless+BayesianSimilarity[sim={self.target_similarity}]"
    
    def build(self):
        os.chdir(PROJECT_DIR)
        subprocess.run(["cargo", "build", "--release", "--bin", self.binary_name], check=True)
        os.chdir("..") 

                
class PinSketch(Algorithm):
    """Test runner for the PinSketch algorithm."""
    build_dir = os.path.join(PROJECT_DIR, "target", "release")
    binary_name = "pinsketch"

    def run(self):
        print(f"--- Running tests for: {self.to_string()} ---")
        cmd = [
            os.path.join(self.build_dir, self.binary_name),
            f"{TEST_DATA_DIR}/{TEST_NAME}",
            str(NR_TESTS),
            f"{RESULTS_DIR}/{TEST_NAME}",
        ]
        subprocess.run(cmd, check=True)

    def to_string(self) -> str:
        return "PinSketch"

    def build(self):
        os.chdir(PROJECT_DIR)
        subprocess.run(["cargo", "build", "--release", "--bin", self.binary_name], check=True)
        os.chdir("..")
        
class FullStateTransfer(Algorithm):
    """Test runner for the FullStateTransfer algorithm."""
    build_dir = os.path.join(PROJECT_DIR, "target", "release")
    binary_name = "full_state_transfer"

    def run(self):
        print(f"--- Running tests for: {self.to_string()} ---")
        cmd = [
            os.path.join(self.build_dir, self.binary_name),
            f"{TEST_DATA_DIR}/{TEST_NAME}",
            str(NR_TESTS),
            f"{RESULTS_DIR}/{TEST_NAME}",
        ]
        subprocess.run(cmd, check=True)

    def to_string(self) -> str:
        return "FullStateTransfer"

    def build(self):
        os.chdir(PROJECT_DIR)
        subprocess.run(["cargo", "build", "--release", "--bin", self.binary_name], check=True)
        os.chdir("..")

class PBS(Algorithm):
    """Test runner for the PinSketch algorithm."""
    
    project_dir = "pbs_organized/reconciliation/PBS"
    binary_name = "pbs_perf"


    def run(self):
        print(f"--- Running tests for: {self.to_string()} ---")
        cmd = [
            os.path.join(self.project_dir,"build", self.binary_name),
            f"{TEST_DATA_DIR}/{TEST_NAME}",
            str(NR_TESTS),
            f"{RESULTS_DIR}/{TEST_NAME}",
        ]
        subprocess.run(cmd, check=True)

    def to_string(self) -> str:
        return "PBS"

    
    def build(self):
        os.chdir(self.project_dir)
        subprocess.run(["make"], check=True)
        os.chdir("../../..")

class BF_RIBLT(Algorithm):
    """Test runner for the BF_RIBLT algorithm, which includes an FPR value."""
    build_dir = os.path.join(PROJECT_DIR, "target", "release")
    binary_name = "bf_riblt"

    def __init__(self, fpr):
        self.fpr = fpr

    def run(self):
        print(f"--- Running tests for: {self.to_string()} ---")
        cmd = [
            os.path.join(self.build_dir, self.binary_name),
            f"{TEST_DATA_DIR}/{TEST_NAME}",
            str(NR_TESTS),
            f"{RESULTS_DIR}/{TEST_NAME}",
            str(self.fpr)
        ]
        subprocess.run(cmd, check=True)
    
    def to_string(self) -> str:
        return f"Bloom+Rateless[fpr={self.fpr*100:.1f}%]"

    def build(self):
        os.chdir(PROJECT_DIR)
        subprocess.run(["cargo", "build", "--release", "--bin", self.binary_name], check=True)
        os.chdir("..")
        
def ensure_test_data_similarity(set_generator_path):
    if TEST_NAME=="similarity":
        start_similarity = 0
        end_similarity = 1.0
        nr_steps = 20
    elif TEST_NAME=="small_d":
        start_similarity = 0.85
        end_similarity = 1.0
        nr_steps = 30
    else:
        raise Exception(f"Test name {TEST_NAME} not supported")
    
    tow_estimator = TowEstimator()
    tow_estimator.build()
    
    for step in range(nr_steps+1):
        similarity = start_similarity + (step/nr_steps)*(end_similarity-start_similarity)        
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
                "--test-type", "similarity"
            ]
            subprocess.run(cmd, check=True)
        
        if nr_differences==0:
            continue
        
        for test in range(NR_TESTS):
            test_folder = f"{TEST_DATA_DIR}/{TEST_NAME}/d_{nr_differences}/test_{test}"
            if not os.path.exists(f"{test_folder}/tow_estimate.txt"):
                tow_estimator.run(nr_differences, test)
                
            if not os.path.exists(f"{test_folder}/params.txt"):
                with open(f"{test_folder}/tow_estimate.txt", 'r') as file:
                    file_content = file.read()
                
                diff = float(file_content.strip())
                scaled_diff = int(math.ceil(diff * INF_RATIO))

                (opt_prob, opt_n, opt_t) = get_best_param(scaled_diff, AVG_DIFF, MAX_ROUND, SPLIT_NUM, TARGET_SUCCESS_RATE)
                
                with open(f"{test_folder}/params.txt", 'w') as f:
                    f.write(f'{opt_prob} {opt_n} {opt_t}')
                

def ensure_test_data():
    """Checks for test data and generates it if it's missing."""
    print("Generating test data.")
    # Build the set_generator binary
    os.chdir(PROJECT_DIR)
    subprocess.run(["cargo", "build", "--release", "--bin", "set_generator"], check=True)
    os.chdir("..")

    # Run the generator
    set_generator_path = os.path.join(PROJECT_DIR, "target", "release", "set_generator")
    if TEST_NAME=="similarity" or TEST_NAME=="small_d":
        ensure_test_data_similarity(set_generator_path)
    else:
        raise Exception(f"Test name {TEST_NAME} not supported")


def main():
    """Main function to orchestrate the test run."""
    print("--- Clearing old results and preparing directory ---")
    ensure_test_data()

    print("--- Running all tests ---")
        
    algorithms: list[Algorithm] = []
    
    if TEST_NAME=="similarity":
        #fpr from 0.5% to 50% with 5% increments
        algorithms  += [BF_RIBLT(fpr_times_two / 200) for fpr_times_two in range(1, 101)]

    algorithms += [
        PinSketch(),
        RIBLT(),
        RBF_RIBLT_EXPECTED_COST(),
        PBS(),
        FullStateTransfer()
    ]
    
    for algo in algorithms:
        results_file = f"{RESULTS_DIR}/{TEST_NAME}/{algo.to_string()}.csv"
        if os.path.isfile(results_file):
            print(f"Results found, skipping test for {algo.to_string()}")
            continue
        algo.build()
        algo.run()

    print("--- All tests finished ---")
    print(f"Results are available in {RESULTS_DIR}")

if __name__ == "__main__":
    main()
