pub mod algorithms;

use std::collections::HashSet;

use rand::{
    distributions::{Alphanumeric, DistString, Distribution, Uniform}, rngs::StdRng, seq::SliceRandom
};
fn sets_with(len: usize, similarity: f64, rng: &mut StdRng) -> (Vec<String>, Vec<String>) {
    assert!(
        (0.0..=1.0).contains(&similarity),
        "similarity ratio should be in (0.0..=1.0)"
    );

    //derived such that sims/(sims+2*diffs) = similarity
    let sims = ((2.0 * similarity * len as f64) / (1.0 + similarity)) as usize;
    let diffs = len - sims;

    let dist = Uniform::new_inclusive(5, 80);

    let mut global_seen = HashSet::new();
    let (mut local, mut remote) = (Vec::new(), Vec::new());
    
    for _ in 0..sims {
        let item = loop {
            let len = dist.sample(rng);
            let item = Alphanumeric.sample_string(rng, len);
            if global_seen.insert(item.clone()) {
                break item;
            }
        };
        local.push(item.clone());
        remote.push(item);
    }
    
    for _ in 0..diffs {
        let item = loop {
            let len = dist.sample(rng);
            let item = Alphanumeric.sample_string(rng, len);
            if global_seen.insert(item.clone()) {
                break item;
            }
        };
        local.push(item);
    
        let item = loop {
            let len = dist.sample(rng);
            let item = Alphanumeric.sample_string(rng, len);
            if global_seen.insert(item.clone()) {
                break item;
            }
        };
        remote.push(item);
    }

    local.shuffle(rng);
    remote.shuffle(rng);

    (local, remote)
}