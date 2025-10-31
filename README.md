# Rateless Bloom Filters (RBFs) Implementation

This repository provides an implementation of **Rateless Bloom Filters (RBFs)**, a novel solution to the set reconciliation problem, specifically in scenarios involving **variable-sized elements**.

## The Core Problem: Inefficient Reconciliation for Variable-Sized Elements

In many distributed systems, reconciliation protocols must handle elements of variable size (e.g., files, database records, bitcoin transactions). When traditional set reconciliation protocols are adapted for this case, they synchronize fixed-size digests of the elements.

This approach becomes inefficient when the number of differences (**d**) is not very small, as the communication cost is proportional to the size of the element digest ($O(d \cdot \text{digest\_size})$). This high overhead is especially problematic after major events like network partitions or extended replica downtime.

### The Trade-Off Challenge

A common space-efficient approach is to use a **Bloom filter (BF)** as a preliminary step to identify most differences, leaving only a small, predictable number of **false positives** for a final, robust reconciliation stage (e.g., using protocols like RIBLTs).

The BF is significantly smaller than the direct exchange of element digests when the number of differences ($\mathbf{d}$) is not very small.

> **Example:** If a Bloom filter uses 4 bits per element, and the element digest size is 64 bits, the BF is more space-efficient than exchanging $d$ digests when $4 \cdot n < d \cdot 64$, or when **$d > n/16$** ($n$ being the total set size). As such, when $d$ is not small, a Bloom filter is a highly space-efficient way to detect most differing elements.

The problem is that the optimal BF configuration (its size and the number of hash functions) depends entirely on the unknown difference cardinality ($\mathbf{d}$).

* If $d$ is **very small**, a highly precise BF is inefficient, and a simple digest exchange might be better.
* If $d$ is **very large**, a highly precise BF is optimal to minimize false positives.

However, this introduces a problem: the optimal configuration (size and number of hash functions) of the initial Bloom filter depends entirely on the unknown **d**.


## The Solution: Rateless Bloom Filters (RBFs)

RBFs eliminate the need for any prior parameter estimation.


RBFs define an infinite sequence of small BFs (slices) that are streamed iteratively. By design, the RBF approach **naturally adapts to any possible set overlap** as the slices are consumed. The result is a communication cost that **closely follows an optimally configured static Bloom filter** across the entire range of set differences, but without ever needing to estimate the difference cardinality ($\mathbf{d}$).

-----


## Quick Start: Reproducing Experiments

For users interested in quickly reproducing the experimental results from the associated research paper, follow these steps.

### 1\. Install Dependencies 🛠️

You will need the following development tools and libraries:

  * **Rust** and **Cargo** (for the developed algorithms).
  * **Python 3** and the **`matplotlib`** library (for running the orchestrator script and generating plots).
  * **C++ Compiler (`g++`)** and other **external dependencies** required by the PBS code, which can be consulted in the **`pbs_organized`** directory.


### 2\. Run the Experiments and Build Binaries 🧪

Use the Python orchestration script to generate test data and run all algorithms. This script automatically handles the necessary building of all Rust and C++ executables before running the tests.

We will run the **full-range** experiment (0% to 100% similarity) as an example.

```bash
python scripts/run_tests.py full_range
```

> 💡 This command will:
>
>   * Generate the **test data** (in `./test_data/full_range`).
>   * **Build** all algorithm binaries (RBF, PBS, etc.).
>   * Run all algorithms against the data.
>   * Produce the necessary CSV results files in the designated results folder (`./results/full_range`).
>
> It automatically avoids duplicated work (skipping build, data generation, or execution if results already exist).

### 3\. Generate Plots 📊

Use the plotting script to read the generated CSV results and create the final graphs. You must point it to the parent results directory.

```bash
# Use --help to see specific plotting options
python scripts/plots.py ./results
```
-----

## Detailed Documentation: System Overview

This section is for researchers and developers who wish to understand the internal structure, extend the system, or validate specific components.

### Repository Structure

The repository maintains a clean separation between third-party code, developed algorithms, and orchestration scripts:

| Directory | Content Description |
| :--- | :--- |
| **`pbs_organized`** | Contains C++ code adapted from the original **PBS (Parity Bitmap Sketch)** paper, specifically the **ToW estimator** and the **PBS algorithm**. |
| **`xp`** | Houses all the **Rust code** developed for this work. The `bin` folder within `xp` contains multiple files, each compiling into a separate executable. These include the primary **`set_generator`** and the binaries for the implemented set reconciliation **algorithms** (RIBLTs, RBF+RIBLT, PinSketch, etc). |
| **`scripts`** | Contains Python scripts essential for orchestrating the experiments and processing the results. |

-----

### Experimental Workflow and Scripts

The experiment pipeline is managed primarily by Python scripts in the `scripts` folder, providing robust automation and ensuring reproducible results.

#### `run_tests.py`: The Experiment Orchestrator

The `run_tests.py` script manages the entire flow, from data generation to algorithm execution. It accepts an argument to specify the experiment range:

  * **`full_range`**: Tests set similarities from 0% to 100% (with defined increments).
  * **`high_similarity`**: Tests set similarities from 85% to 100% (with finer increments).

The script provides a common interface for each algorithm via two core methods:

  * **`build`**: Compiles the executable for the specified algorithm.
  * **`run`**: Executes the algorithm against all generated input data.

**Duplication Avoidance:** `run_tests.py` is designed for efficiency:

  * It skips data generation if the **test data folder** already exists.
  * It skips running an algorithm if its final **CSV result file** already exists.

#### Stage 1: Test Data Generation

The `run_tests.py` script first runs the **`set_generator`** binary to create the input data, organized within the **`test_data`** folder.

The data is structured based on the required number of differences ($d$) to achieve the target set similarity:

1.  **Similarity Folder:** For each calculated difference count, a main folder is created: **`d_{number_of_differences}`**.
2.  **Test Folders:** For statistical validity (e.g., typically 30 tests, but customizable), a folder is created for each generated pair of sets: **`test_{i}`**.
3.  **Data Files:** Within each `test_{i}` folder, three files store the set components: one for the **common elements**, one for the **local-only elements**, and one for the **remote-only elements**.

#### Stage 2: Estimating Parameters (For Adaptive Algorithms)

Before running all algorithms, `run_tests.py` generates the necessary parameters for algorithms that require an *a priori* estimate of the difference count (e.g., PBS).

1.  **ToW Estimation:** If the **`tow_estimate.txt`** file doesn't exist, the script runs the **ToW estimator** on the replica pair and stores the estimated difference count ($d$) in this file.
2.  **PBS Parameter Calculation:** If the **`params.txt`** file doesn't exist, the script uses the code within the **`scripts/PBS`** folder to calculate the **optimal parameters** for PBS, leveraging the $d$ estimate. These parameters are stored in **`params.txt`** and subsequently used by the PBS executable.

#### Stage 3: Algorithm Execution and Results

With all data and parameters ready, the `run_tests.py` script executes the `run` method for every algorithm.

  * Each algorithm executable is provided the **`test_data`** folder as input.
  * It executes the algorithm for **every pair of sets** generated.
  * The final output is a **CSV file** per algorithm (e.g., `RBFs.csv`), containing key experiment metrics like **transmitted metadata**, **encoding time**, and **decoding time**, which are parseable by the plotting script.

#### `plots.py`: Visualization

The **`plots.py`** script reads the generated CSV files from the execution stage and uses them to produce the final visual graphs and plots presented in the research paper.

> If you have any questions, [send me an email](mailto:pedromgomes29+github@gmail.com)