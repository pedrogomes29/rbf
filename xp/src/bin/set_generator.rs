
use clap::Parser;
use rand::{distributions::{Alphanumeric, DistString, Uniform}, prelude::Distribution, SeedableRng};
use std::{collections::HashSet, fs::{self, File}, io::Write, path::PathBuf};


#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Args {
    nr_tests: u64,
    nr_elements: usize,
    output_dir: PathBuf,
}


fn main() {
    let args = Args::parse();
    let dist = Uniform::new_inclusive(5, 80);
    let mut global_seen = HashSet::new();

    fs::create_dir_all(&args.output_dir).expect("Failed to create output directory");

    for seed in 0..args.nr_tests {
        let mut rng = rand::rngs::StdRng::seed_from_u64(seed); // Use a seed for reproducibility

        let file_path = args.output_dir.join(format!("{}", seed));
        let mut file = File::create(&file_path).expect("Failed to create file");

        for _ in 0..args.nr_elements {
            let item = loop {
                let len = dist.sample(&mut rng);
                let item = Alphanumeric.sample_string(&mut rng, len);
                if global_seen.insert(item.clone()) {
                    break item;
                }
            };
            writeln!(file, "{}", item).expect("Failed to write to file");
        }
    }
}