
use clap::Parser;
use std::path::PathBuf;
use xp::run_test;
use xp::sync::bf_riblt::BloomRIBLT;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Args {
    input_dir: PathBuf,
    seed: usize,
    cardinality: usize,
    d: usize,
    results_dir: PathBuf,
    fpr: f64
}


fn main(){
    let args = Args::parse();
    let algo = BloomRIBLT::new(args.fpr);

    run_test::<String, _>(
        &algo,
        &args.input_dir,
        args.seed,
        args.cardinality,
        args.d,
        &args.results_dir
    );
}