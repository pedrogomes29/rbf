use clap::Parser;
use rand::{
    Rng, SeedableRng,
    distributions::{Alphanumeric, DistString, Distribution, Uniform},
};
use std::{
    collections::HashSet,
    fs::{self, File},
    io::Write,
    path::PathBuf,
};

#[derive(Parser, Debug)]
#[command(
    author,
    version,
    about = "Generates test data for set reconciliation algorithms."
)]
struct Args {
    /// The number of tests to generate for each configuration.
    #[arg(short, long)]
    nr_tests: u64,

    /// The number of elements in the larger set.
    #[arg(short, long)]
    set_cardinality: usize,

    /// The number of differences between the local and remote sets.
    #[arg(short, long)]
    nr_differences: usize,

    /// The output directory for the generated test data.
    #[arg(short, long)]
    output_dir: PathBuf,

    /// The type of test to generate: 'similarity' or 'subset'.
    #[arg(short, long)]
    test_type: String,
}

fn generate_unique_items(
    rng: &mut impl Rng,
    count: usize,
    seen: &mut HashSet<String>,
) -> Vec<String> {
    let mut items = Vec::with_capacity(count);
    let dist = Uniform::new_inclusive(5, 80);
    while items.len() < count {
        let len = dist.sample(rng);
        let item = Alphanumeric.sample_string(rng, len);
        if seen.insert(item.clone()) {
            items.push(item);
        }
    }
    items
}

fn write_set_to_file(path: &PathBuf, items: &[String]) {
    let mut file = File::create(path).expect("Failed to create file");
    for item in items {
        writeln!(file, "{}", item).expect("Failed to write to file");
    }
}

fn generate_similarity_test(args: &Args, seed: u64, global_seen: &mut HashSet<String>) {
    let mut rng = rand::rngs::StdRng::seed_from_u64(seed);

    // Differences are split evenly between local and remote
    let local_diffs = args.nr_differences / 2;
    let remote_diffs = args.nr_differences - local_diffs;
    let common_size = args.set_cardinality - local_diffs;

    let common_items = generate_unique_items(&mut rng, common_size, global_seen);
    let local_only_items = generate_unique_items(&mut rng, local_diffs, global_seen);
    let remote_only_items = generate_unique_items(&mut rng, remote_diffs, global_seen);

    // Create the output directory for this specific test
    let test_dir = args.output_dir.join(format!("test_{}", seed));
    fs::create_dir_all(&test_dir).expect("Failed to create output directory for test");

    // Write the three sets to their own files
    write_set_to_file(&test_dir.join("common"), &common_items);
    write_set_to_file(&test_dir.join("local_only"), &local_only_items);
    write_set_to_file(&test_dir.join("remote_only"), &remote_only_items);
}

fn generate_subset_test(args: &Args, seed: u64, global_seen: &mut HashSet<String>) {
    let mut rng = rand::rngs::StdRng::seed_from_u64(seed);

    let local_size = args.set_cardinality - args.nr_differences;
    let remote_diffs = args.nr_differences;

    // The local set is the 'common' set of the two
    let common_items = generate_unique_items(&mut rng, local_size, global_seen);
    // Remote-only items are the differences
    let remote_only_items = generate_unique_items(&mut rng, remote_diffs, global_seen);
    // The local_only set is empty in a subset test
    let local_only_items: Vec<String> = Vec::new();

    // Create the output directory for this specific test
    let test_dir = args.output_dir.join(format!("test_{}", seed));
    fs::create_dir_all(&test_dir).expect("Failed to create output directory for test");

    // Write the three sets to their own files
    write_set_to_file(&test_dir.join("common"), &common_items);
    write_set_to_file(&test_dir.join("local_only"), &local_only_items);
    write_set_to_file(&test_dir.join("remote_only"), &remote_only_items);
}

fn main() {
    let args = Args::parse();
    let mut global_seen = HashSet::new();

    for seed in 0..args.nr_tests {
        match args.test_type.as_str() {
            "similarity" => generate_similarity_test(&args, seed, &mut global_seen),
            "subset" => generate_subset_test(&args, seed, &mut global_seen),
            _ => panic!("Invalid test_type. Please use 'similarity' or 'subset'."),
        }
    }
}
