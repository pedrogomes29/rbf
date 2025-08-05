#![allow(dead_code)]

use std::{
    collections::HashSet, f64::consts::LN_2, fmt::Display, hash::Hash, time::{Duration, Instant}
};

use crate::{
    benchmarks::sets_with, rateless_bloom::{angle_heuristic::AngleHeuristicFactory, bayesian_no_params::{BayesianNoParams, BayesianNoParamsFactory}, bayesian_similarity::BayesianSimilarityFactory, StoppingStrategyFactory}, sync::{
        bf_riblt::BloomRIBLT, rbf_riblt::RBloomRIBLT, riblt::RIBLT, Algorithm, Measure
    }, tracker::{Bandwidth, DefaultEvent, DefaultTracker, Telemetry}
};

use rand::{SeedableRng, rngs::StdRng};

const NR_TRIALS:usize = 5;

type Replica<T> = (Vec<T>, Bandwidth);

//creates a vector of events corresponding to the average event for each message over multiple experiments
fn average_tracker_events(
    message_to_events: Vec<Vec<DefaultEvent>>,
    nr_experiments: usize,
    upload: Bandwidth,
    download: Bandwidth,
) -> Vec<DefaultEvent> {
    message_to_events
        .into_iter()
        .map(|message_events| {
            let (total_state, total_metadata): (usize, usize) = message_events.iter().fold((0, 0), |(s, m), e| {
                let (event_state, event_metadata) = match e {
                    DefaultEvent::LocalToRemote { state, metadata, .. }
                    | DefaultEvent::RemoteToLocal { state, metadata, .. } => (*state, *metadata),
                };
                (s + event_state, m + event_metadata)
            });

            let avg_state = total_state / nr_experiments;
            let avg_metadata = total_metadata / nr_experiments;

            match message_events.first().expect("Expected at least one event") {
                DefaultEvent::LocalToRemote { .. } => {
                    DefaultEvent::LocalToRemote { state: avg_state, metadata: avg_metadata, upload }
                }
                DefaultEvent::RemoteToLocal { .. } => {
                    DefaultEvent::RemoteToLocal { state: avg_state, metadata: avg_metadata, download }
                }
            }
        })
        .collect()
}


/// Runs the specified protocol and outputs the metrics obtained.
fn run<T, A>(algo: &A, similar: f64, local: Replica<T>, remote: Replica<T>) -> DefaultTracker
where
    T: Clone,
    A: Algorithm<T, Tracker = DefaultTracker> + Display,
{
    assert!(
        (0.0..=1.0).contains(&similar),
        "similarity should be a ratio between 0.0 and 1.0"
    );

    let (local, upload) = local;
    let (remote, download) = remote;

    let mut tracker = DefaultTracker::new(download, upload);
    algo.sync(local, remote, &mut tracker);

    let diffs = tracker.false_matches();
    if diffs > 0 {
        panic!("{algo} not totally synced with {diffs} false matches");
    }

    tracker
}

fn run_trial<T,A>(algo: &A, similar: f64, replicas: Vec<(Vec<T>,Vec<T>)>, upload:Bandwidth, download:Bandwidth)
where
    T: Clone,
    A: Algorithm<T, Tracker = DefaultTracker> + Display,
{
    let nr_experiments = replicas.len();
    let message_to_events = replicas.into_iter().enumerate().fold(
        Vec::<Vec<DefaultEvent>>::new(),
        |mut acc, (trial_nr, (local, remote))| {
            let tracker = run(
                algo,
                similar,
                (local, upload),
                (remote, download),
            );
            for (idx, event) in tracker.events().iter().cloned().enumerate() {
                if idx == acc.len() {
                    acc.push(Vec::new());
                }
                acc[idx].push(event);
            }
            acc
        },
    );
    
    let events = average_tracker_events(message_to_events, nr_experiments, upload, download);

    println!(
        "{algo} {} {} {:.3}",
        events.iter().map(DefaultEvent::state).sum::<usize>(),
        events.iter().map(DefaultEvent::metadata).sum::<usize>(),
        events
            .iter()
            .filter_map(|e| e.duration().ok())
            .sum::<Duration>()
            .as_secs_f64(),
    );

}



fn run_with<T>(similar: f64, replicas: Vec<(Vec<T>,Vec<T>)>)
where
    T: Clone + Hash + Measure + Eq,
{   

    let total_sum_of_differences_size: usize = replicas
        .iter()
        .map(|(local_vec, remote_vec)| {
            let local_set: HashSet<T> = local_vec.iter().cloned().collect();
            let remote_set: HashSet<T> = remote_vec.iter().cloned().collect();

            // Elements only in local_vec
            let local_only_size: usize = local_set
                .difference(&remote_set)
                .map(|item| T::size_of(&item))
                .sum();

            // Elements only in remote_vec
            let remote_only_size: usize = remote_set
                .difference(&local_set)
                .map(|item| T::size_of(&item))
                .sum();

            local_only_size + remote_only_size
        })
        .sum();

    let theoretical_minimum: usize = if replicas.is_empty() {
        0 // Avoid division by zero if replicas is empty
    } else {
        total_sum_of_differences_size / replicas.len()
    };

    let links = [
        //(Bandwidth::Mbps(10.0), Bandwidth::Mbps(1.0)),
        (Bandwidth::Mbps(10.0), Bandwidth::Mbps(10.0)),
        //(Bandwidth::Mbps(1.0), Bandwidth::Mbps(10.0)),
    ];

    for (upload, download) in links {
        println!(
            "\n{theoretical_minimum} {} {}",
            upload.bits_per_sec(),
            download.bits_per_sec()
        );
        
        let algo = RIBLT::new();
        run_trial(
            &algo,
            similar,
            replicas.clone(),
            upload,
            download
        );

        for fpr in [0.01, 0.1, 0.25] {
            let algo = BloomRIBLT::new(fpr);
            run_trial(
                &algo,
                similar,
                replicas.clone(),
                upload,
                download,
            );
        }

        for m_ratio in [1.0/LN_2] {
            let stopping_strategy_factory = BayesianNoParamsFactory::new(m_ratio);
            let algo = RBloomRIBLT::new(m_ratio, stopping_strategy_factory);

            run_trial(
                &algo,
                similar,
                replicas.clone(),
                upload,
                download
            );
        }
    }
}

fn run_experiment<T, F>(label: &str, nr_trials: usize, create_replicas: F)
where
    T: Clone + Hash + Measure + Eq,
    F: Fn(f64) -> (Vec<T>, Vec<T>),
{
    let exec_time = Instant::now();
    let nr_steps = 18;
    let start_similarity = 10;
    let end_similarity = 100;
    let step = ((end_similarity - start_similarity) as f64) / nr_steps as f64;

    let similarities = (0..=nr_steps)
        .map(|i| start_similarity as f64 + i as f64 * step)
        .map(|val| val / 100.0);

    println!("{start_similarity} {end_similarity} {nr_steps}");

    for s in similarities {
        let replicas: Vec<_>= (0..nr_trials).map(|_|create_replicas(s)).collect();
        eprintln!(
            "[{:.2?}] {label} with similarity {s} generated",
            exec_time.elapsed()
        );
        run_with(s, replicas);
    }

    eprintln!("[{:.2?}] exiting...", exec_time.elapsed());
}

pub fn run_variable_size_experiment() {
    run_experiment("variable_size", NR_TRIALS, |s| {
        let mut rng = StdRng::seed_from_u64(rand::random());
        sets_with(100_000, s, &mut rng)
    });
}