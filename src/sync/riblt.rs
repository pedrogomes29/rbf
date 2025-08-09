use std::{collections::{HashMap, HashSet}, fmt::Display, hash::RandomState, marker::PhantomData, mem, time::Instant};

use crate::{
    riblt::{RatelessIBLT, Symbol}, sync::Measure, tracker::{DefaultTracker, Telemetry}
};

use std::hash::{Hash, BuildHasher};

use super::{Algorithm, BuildRatelessIBLT};

pub struct RIBLT<T> {
    _marker: PhantomData<T>,
}

impl<T> RIBLT<T> {
    #[inline]
    #[must_use]
    pub fn new() -> Self {
        Self {
            _marker: PhantomData,
        }
    }
}

impl<T> Display for RIBLT<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Rateless")
    }
}

impl<T> BuildRatelessIBLT<T> for RIBLT<T> where T: Symbol {}

impl<T> Algorithm<T> for RIBLT<T>
where
    T: Clone + Hash + Measure + Eq,
{
    type Tracker = DefaultTracker;

    fn sync(&self, mut local: Vec<T>, mut remote: Vec<T>, tracker: &mut Self::Tracker) {
        const CODED_SYMBOL_SIZE: usize =
            mem::size_of::<u64>() + mem::size_of::<u64>() + mem::size_of::<i64>();

        assert!(
            tracker.is_ready(),
            "tracker should be ready, i.e., no captured events and not finished"
        );

        // 1. Create a rateless IBLT from the hash of the local join-deocompositions and send it
        //    to the remote replica.
        let hasher = RandomState::new();
        let mut local_hashes = HashMap::new();

        let exec_time = Instant::now();
        local.iter().cloned().for_each(|e| {
            let item_hash = hasher.hash_one(&e);
            local_hashes.insert(item_hash, e);
        });
        let t_enc_local_elements_to_hashes = exec_time.elapsed();



        let mut local_iblt = RatelessIBLT::riblt_from(local_hashes.keys().cloned());

        // 2. Repeat the procedure from 1., but now on the remote replica.
        let mut remote_hashes = HashMap::new();

        let exec_time = Instant::now();
        remote.iter().cloned().for_each(|e| {
            let item_hash = hasher.hash_one(&e);
            remote_hashes.insert(item_hash, e);
        });
        let t_enc_remote_elements_to_hashes = exec_time.elapsed();


        let mut remote_iblt = RatelessIBLT::riblt_from(remote_hashes.keys().cloned());

        // 3. Send Coded symbols until the remote replica has enough to decode all the differences
        remote_iblt.find_all_differences(&mut local_iblt);
        let sketch_size = local_iblt.sketch.len();
        assert_eq!(sketch_size, remote_iblt.sketch.len());

        tracker.increment_metadata(sketch_size * CODED_SYMBOL_SIZE);

        let remote_only_hashes = remote_iblt.get_local_only_symbols();
        let local_only_hashes = remote_iblt.get_remote_only_symbols();

        let exec_time = Instant::now();
        let remote_only_elements: Vec<_> = remote_only_hashes
            .into_iter()
            .map(|hash| remote_hashes[&hash].clone())
            .collect();
        let t_dec_remote_hashes_to_elem = exec_time.elapsed();



        // 4. Send remote only state corresponding to remote only hashes,
        //    Send local only hashes to request for local only state
        tracker.increment_state(
            remote_only_elements
                .iter()
                .map(<T as Measure>::size_of)
                .sum()
        );
        tracker.increment_metadata(local_only_hashes.iter().count() * mem::size_of::<u64>());

        let exec_time = Instant::now();
        let local_only_elements: Vec<_> = local_only_hashes
            .into_iter()
            .map(|hash| local_hashes[&hash].clone())
            .collect();
        let t_dec_local_hashes_to_elem = exec_time.elapsed();


        // 5. Send local only state corresponding to local only hashes,
        tracker.increment_state(
            local_only_elements
                .iter()
                .map(<T as Measure>::size_of)
                .sum(),
        );

        tracker.increment_t_enc(
            remote_iblt.t_enc()
            + t_enc_local_elements_to_hashes
            + t_enc_remote_elements_to_hashes
        );

        tracker.increment_t_dec(
            remote_iblt.t_dec()
            + t_dec_local_hashes_to_elem
            + t_dec_remote_hashes_to_elem
        );

        // 9. Sanity Check
        local.extend(remote_only_elements);
        remote.extend(local_only_elements);


        let local_set: HashSet<T> = local.into_iter().collect();
        let remote_set: HashSet<T> = remote.into_iter().collect();

        // Elements only in local_vec
        let local_only = local_set
            .difference(&remote_set);

        // Elements only in remote_vec
        let remote_only = remote_set
            .difference(&local_set);

        let false_matches = local_only.count() + remote_only.count();
        tracker.finish(false_matches);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sync() {
        let local = {
            let mut local = Vec::new();
            let items = "a b c d e f g h i j k l"
                .split_whitespace()
                .collect::<Vec<_>>();

            for item in items {
                local.push(item.to_string());
            }

            local
        };

        let remote = {
            let mut remote = Vec::new();
            let items = "m n o p q r s t u v w x y z"
                .split_whitespace()
                .collect::<Vec<_>>();

            for item in items {
                remote.push(item.to_string());
            }

            remote
        };
        let mut tracker = DefaultTracker::new();
        let buckets = RIBLT::new();

        buckets.sync(local, remote, &mut tracker);

        assert_eq!(tracker.false_matches(), 0);
    }
}
