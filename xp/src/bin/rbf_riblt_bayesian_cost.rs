use clap::Parser;
use std::f64::consts::LN_2;
use std::path::PathBuf;
use xp::rateless_bloom::bayesian_cost::BayesianCostFactory;
use xp::run_test;
use xp::sync::rbf_riblt::RBloomRIBLT;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Args {
    input_dir: PathBuf,
    nr_tests: usize,
    results_dir: PathBuf,
}

fn main() {
    let args = Args::parse();

    let optimal_m_ratio = 1.0 / LN_2;
    let stopping_strategy_factory = BayesianCostFactory::new(optimal_m_ratio);
    let algo = RBloomRIBLT::new(optimal_m_ratio, stopping_strategy_factory);

    run_test::<String, _>(&algo, &args.input_dir, args.nr_tests, &args.results_dir);
}
