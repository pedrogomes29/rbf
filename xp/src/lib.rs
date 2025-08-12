use std::{
    fmt::Display,
    fs::{self, File, OpenOptions},
    hash::Hash,
    io::{self, BufRead, Write},
    path::Path,
    time::Instant,
};

mod bayesian_estimation;
mod bloom;
pub mod rateless_bloom;
mod riblt;
pub mod sync;
mod tracker;

use crate::{
    sync::{Algorithm, Measure},
    tracker::{DefaultTracker, Telemetry},
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

fn read_file_to_vec(path: &Path) -> io::Result<Vec<String>> {
    let file = File::open(path)?;
    let reader = io::BufReader::new(file);
    let lines: io::Result<Vec<String>> = reader.lines().collect();
    lines
}

pub fn run_test<T, A>(algo: &A, input_dir: &Path, nr_tests: usize, results_dir: &Path)
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

    let d_dirs = fs::read_dir(&input_dir)
        .expect("Failed to read test type directory")
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let path = entry.path();
            if path.is_dir() && path.file_name()?.to_str()?.starts_with("d_") {
                Some(path)
            } else {
                None
            }
        });

    for (d_idx, d_dir) in d_dirs.enumerate() {
        // Parse the 'd' value from the directory name (e.g., "d_6000" -> 6000.0).
        let d_str = d_dir
            .file_name()
            .unwrap()
            .to_str()
            .unwrap()
            .trim_start_matches("d_");
        let d: usize = d_str
            .parse()
            .expect("Failed to parse 'd' from directory name");

        println!("Running tests with d = {d} (index = {d_idx})");
        let exec_time = Instant::now();

        for test_nr in 0..nr_tests {
            let test_dir = d_dir.join(format!("test_{test_nr}"));

            let common_path = test_dir.join("common");
            let local_only_path = test_dir.join("local_only");
            let remote_only_path = test_dir.join("remote_only");

            // Read the sets from the files.
            let common_strings = read_file_to_vec(&common_path).expect("Failed to read local file");
            let local_only_strings =
                read_file_to_vec(&local_only_path).expect("Failed to read local file");
            let remote_only_strings =
                read_file_to_vec(&remote_only_path).expect("Failed to read remote file");

            // Convert Vec<String> to Vec<T> using the From<String> trait.
            let local: Vec<T> = common_strings
                .iter()
                .chain(local_only_strings.iter())
                .map(|s| s.clone().into())
                .collect();

            let remote: Vec<T> = common_strings
                .iter()
                .chain(remote_only_strings.iter())
                .map(|s| s.clone().into())
                .collect();

            let tracker = run(algo, local, remote);

            // Write the results to the file.
            writeln!(
                &mut results_file,
                "{:.2},{},{},{},{}",
                d,
                tracker.state(),
                tracker.metadata(),
                tracker.t_enc().as_nanos(),
                tracker.t_dec().as_nanos()
            )
            .unwrap();
        }

        println!("Took {:.2?}", exec_time.elapsed())
    }
}
