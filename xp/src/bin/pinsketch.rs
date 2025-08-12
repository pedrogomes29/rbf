use clap::Parser;
use std::path::PathBuf;
use xp::run_test;
use xp::sync::pinsketch::PinSketch;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Args {
    input_dir: PathBuf,
    nr_tests: usize,
    results_dir: PathBuf,
}

fn main() {
    let args = Args::parse();
    let algo = PinSketch::new();
    run_test::<String, _>(&algo, &args.input_dir, args.nr_tests, &args.results_dir);
}
