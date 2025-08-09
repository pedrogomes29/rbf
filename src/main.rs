#![allow(dead_code)]

use std::{env, fs, path::PathBuf};

use crate::benchmarks::algorithms;

mod benchmarks;
mod bloom;
mod rateless_bloom;
mod riblt;
mod sync;
mod tracker;
mod bayesian_estimation;

/// Entry point for the execution of the experiments.
///
/// The first experiment is on similar uses replica with the same cardinality and a given degree of
/// similarity. Furthermore, we repeat this experiment on different link configurations with both
/// symmetric and assymetric channels.
///
/// The second experiment is on replicas of distinct cardinalities, also with different link
/// configurations, again, with both symmetric and asymmetric channels.
///
/// The third experiment tests rateless bloom filters (TODO: better explanation)
fn main() {
    let args = env::args().collect::<Vec<_>>();
    if args.len() != 2 {
        panic!("expected an argument telling which data type to use")
    }

    let results_dir = PathBuf::from(args[1].to_lowercase());
    fs::create_dir_all(&results_dir).expect("Expected to open results dir succesfully");
    algorithms::run_variable_size_experiment(&results_dir);
}
