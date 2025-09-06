use clap::Parser;
use xp::sync::full_state_transfer::FullStateTransfer;
use std::path::PathBuf;
use xp::run_test;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Args {
    input_dir: PathBuf,
    nr_tests: usize,
    results_dir: PathBuf,
}

fn main() {
    let args = Args::parse();
    let algo = FullStateTransfer::new();
    run_test::<String, _>(&algo, &args.input_dir, args.nr_tests, &args.results_dir);
}
