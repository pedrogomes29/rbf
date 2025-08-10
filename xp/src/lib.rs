use std::{
    fmt::Display, fs::{File, OpenOptions}, hash::Hash, io::{BufRead, BufReader, Write}, path::Path
};

mod bloom;
pub mod rateless_bloom;
mod riblt;
pub mod sync;
mod tracker;
mod bayesian_estimation;

use crate::{
    sync::{Algorithm, Measure}, 
    tracker::{
        DefaultTracker, Telemetry
    }
};

/// Runs the specified protocol and outputs the metrics obtained.
fn run<T, A>(algo: &A, local: Vec<T>, remote: Vec<T>) -> DefaultTracker
where
    T: Clone,
    A: Algorithm<T, Tracker = DefaultTracker> + Display,
{
    let mut tracker = DefaultTracker::new();
    algo.sync(local, remote, &mut tracker);

    let diffs = tracker.false_matches();
    if diffs > 0 {
        panic!("{algo} not totally synced with {diffs} false matches");
    }

    tracker
}



pub fn run_test<T, A>(algo: &A, input_dir: &Path, seed: usize, cardinality: usize, d: usize, results_dir: &Path)
where
    T: Clone + Hash + Measure + Eq + From<String>,
    A: Algorithm<T, Tracker = DefaultTracker> + Display,
{
    let algo_path = results_dir.join(format!("{algo}.csv"));
    let mut results_file = OpenOptions::new()
    .write(true)
    .append(true)
    .create(true)
    .open(&algo_path)
    .expect("Expected to successfully open or create file");

    let input_data_path = input_dir.join(format!("{}", seed));

    let input_data = File::open(&input_data_path)
        .expect(&format!("Failed to open input file: {}", input_data_path.display()));
    let reader = BufReader::new(input_data);

    let mut all_strings: Vec<String> = reader.lines()
        .filter_map(|line| line.ok())
        .collect();
    
    let nlocal_unique = d / 2;
    let nremote_unique = d / 2;
    let ncommon = cardinality - nlocal_unique;
    
    let required_strings = nlocal_unique + nremote_unique + ncommon;
    assert!(
        all_strings.len() >= required_strings,
        "Input file {} does not contain enough strings. Needed: {}, Found: {}",
        input_data_path.display(),
        required_strings,
        all_strings.len()
    );

    let local_unique_part: Vec<String> = all_strings.drain(0..nlocal_unique).collect();
    let remote_unique_part: Vec<String> = all_strings.drain(0..nremote_unique).collect();
    let common_part: Vec<String> = all_strings.drain(0..ncommon).collect();

    // Create the final local and remote sets.
    let mut local: Vec<T> = local_unique_part.into_iter().map(|s| T::from(s)).collect();
    let mut remote: Vec<T> = remote_unique_part.into_iter().map(|s| T::from(s)).collect();

    // Add the common elements to both sets.
    for s in common_part.into_iter() {
        let common_t = T::from(s);
        local.push(common_t.clone());
        remote.push(common_t);
    }

    // Run the reconciliation algorithm and get the tracker.
    let tracker = run(
        algo,
        local,
        remote
    );

    // Write the results to the file.
    writeln!(&mut results_file, "{:.2},{},{},{},{}",
        d,
        tracker.state(),
        tracker.metadata(),
        tracker.t_enc().as_micros(),
        tracker.t_dec().as_micros()
    ).unwrap();
    
}