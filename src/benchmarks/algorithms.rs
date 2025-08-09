#![allow(dead_code)]

use std::{
    f64::consts::LN_2, fmt::Display, fs::File, hash::Hash, io::Write, path::Path, time::Instant
};

use crate::{
    benchmarks::sets_with, rateless_bloom::bayesian_no_params::BayesianNoParamsFactory,
    sync::{
        bf_riblt::BloomRIBLT, rbf_riblt::RBloomRIBLT, riblt::RIBLT, Algorithm, Measure
    }, 
    tracker::{
        DefaultTracker, Telemetry
    }
};

use rand::{SeedableRng, rngs::StdRng};
const NR_TRIALS:usize = 5;

type Replica<T> = (Vec<T>,Vec<T>);

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

fn run_trial<T,A>(algo: &A, similarity_to_replicas: &Vec<(f64, Vec<(Vec<T>, Vec<T>)>)>, results_dir: &Path)
where
    T: Clone,
    A: Algorithm<T, Tracker = DefaultTracker> + Display,
{
    let algo_path = results_dir.join(format!("{algo}.csv"));

    let mut results_file = File::create(&algo_path).expect("Expected to succesfully create file");

    for (similarity, replicas) in similarity_to_replicas{
        eprintln!("Running {} with a similarity of {:.2?}", algo, similarity);
        for (local, remote) in replicas{
            let tracker = run(
                algo,
                local.clone(),
                remote.clone()
            );

            writeln!(&mut results_file, "{:.2},{},{},{},{}",
                similarity,
                tracker.state(),
                tracker.metadata(),
                tracker.t_enc().as_micros(),
                tracker.t_dec().as_micros()
            ).unwrap();
        }
    }
}

fn run_experiment<T, F>(results_dir: &Path, nr_trials: usize, create_replicas: F)
where
    T: Clone + Hash + Measure + Eq,
    F: Fn(f64) -> Replica<T>,
{
    let nr_steps = 20;
    let start_similarity = 0;
    let end_similarity = 100;
    let step = ((end_similarity - start_similarity) as f64) / nr_steps as f64;

    let similarity_to_replicas: Vec<_> = (0..=nr_steps)
        .map(|i| start_similarity as f64 + i as f64 * step)
        .map(|val| val / 100.0)
        .map(|s| {
            let replicas: Vec<_> = (0..nr_trials).map(|_| create_replicas(s)).collect();
            (s, replicas)
        })
        .collect();


    let algo = RIBLT::new();
    run_trial(
        &algo,
        &similarity_to_replicas,
        results_dir
    );

    for fpr in [0.01, 0.1, 0.25] {
        let algo = BloomRIBLT::new(fpr);
        run_trial(
            &algo,
            &similarity_to_replicas,
            results_dir
        );
    }

    let optimal_m_ratio = 1.0/LN_2;
    let stopping_strategy_factory = BayesianNoParamsFactory::new(optimal_m_ratio);
    let algo = RBloomRIBLT::new(optimal_m_ratio, stopping_strategy_factory);
    run_trial(
        &algo,
        &similarity_to_replicas,
        results_dir
    );
}

pub fn run_variable_size_experiment(results_dir: &Path) {
    run_experiment(results_dir, NR_TRIALS, |s| {
        let mut rng = StdRng::seed_from_u64(rand::random());
        sets_with(100_000, s, &mut rng)
    });
}