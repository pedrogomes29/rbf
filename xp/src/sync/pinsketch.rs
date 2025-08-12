use crate::{
    sync::{Algorithm, Measure},
    tracker::{DefaultTracker, Telemetry},
};
use minisketch_rs::Minisketch;
use std::{
    collections::{HashMap, HashSet},
    fmt::Display,
    hash::{BuildHasher, Hash, RandomState},
    marker::PhantomData,
    mem,
    time::{Duration, Instant},
};

const REASONABLE_NR_DIFFS: usize = 30_000;

pub struct PinSketch<T> {
    _marker: PhantomData<T>,
}

impl<T> PinSketch<T> {
    #[inline]
    #[must_use]
    pub fn new() -> Self {
        Self {
            _marker: PhantomData,
        }
    }
}

impl<T> PinSketch<T>
where
    T: Clone + Hash + Measure + Eq,
{
    pub fn derive_transmitted_data(
        &self,
        mut local: Vec<T>,
        mut remote: Vec<T>,
        tracker: &mut <PinSketch<T> as Algorithm<T>>::Tracker,
    ) {
        let hasher = RandomState::new();

        let mut local_hashes = HashMap::new();
        local.iter().cloned().for_each(|e| {
            let item_hash = hasher.hash_one(&e);
            local_hashes.insert(item_hash, e);
        });

        let mut remote_hashes = HashMap::new();
        remote.iter().cloned().for_each(|e| {
            let item_hash = hasher.hash_one(&e);
            remote_hashes.insert(item_hash, e);
        });

        let local_only_hashes: Vec<_> = local_hashes
            .iter()
            .filter(|(k, _)| !remote_hashes.contains_key(k))
            .map(|(k, _)| *k)
            .collect();

        let remote_only_hashes: Vec<_> = remote_hashes
            .iter()
            .filter(|(k, _)| !local_hashes.contains_key(k))
            .map(|(k, _)| *k)
            .collect();

        let nr_diffs = local_only_hashes.len() + remote_only_hashes.len();

        tracker.increment_metadata(nr_diffs * mem::size_of::<u64>());

        let remote_only_elements: Vec<_> = remote_only_hashes
            .into_iter()
            .map(|hash| remote_hashes[&hash].clone())
            .collect();

        // 4. Send remote only state corresponding to remote only hashes,
        //    Send local only hashes to request for local only state
        tracker.increment_state(
            remote_only_elements
                .iter()
                .map(<T as Measure>::size_of)
                .sum(),
        );
        tracker.increment_metadata(local_only_hashes.iter().count() * mem::size_of::<u64>());

        let local_only_elements: Vec<_> = local_only_hashes
            .into_iter()
            .map(|hash| local_hashes[&hash].clone())
            .collect();

        // 5. Send local only state corresponding to local only hashes,
        tracker.increment_state(
            local_only_elements
                .iter()
                .map(<T as Measure>::size_of)
                .sum(),
        );

        // 9. Sanity Check
        local.extend(remote_only_elements);
        remote.extend(local_only_elements);

        let local_set: HashSet<T> = local.into_iter().collect();
        let remote_set: HashSet<T> = remote.into_iter().collect();

        // Elements only in local_vec
        let local_only = local_set.difference(&remote_set);

        // Elements only in remote_vec
        let remote_only = remote_set.difference(&local_set);

        let false_matches = local_only.count() + remote_only.count();
        tracker.finish(false_matches);
    }
}

impl<T> Display for PinSketch<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "PinSketch")
    }
}

impl<T> Algorithm<T> for PinSketch<T>
where
    T: Clone + Hash + Measure + Eq,
{
    type Tracker = DefaultTracker;

    fn sync(&self, mut local: Vec<T>, mut remote: Vec<T>, tracker: &mut Self::Tracker) {
        let local_set: HashSet<_> = local.iter().collect();
        let remote_set: HashSet<_> = remote.iter().collect();

        // Elements only in local_vec
        let local_only = local_set.difference(&remote_set);

        // Elements only in remote_vec
        let remote_only = remote_set.difference(&local_set);

        let nr_diffs = local_only.count() + remote_only.count();

        if nr_diffs > REASONABLE_NR_DIFFS {
            self.derive_transmitted_data(local, remote, tracker);
            return;
        }

        let hasher = RandomState::new();

        let mut local_hashes = HashMap::new();
        let exec_time = Instant::now();
        local.iter().cloned().for_each(|e| {
            let item_hash = hasher.hash_one(&e);
            local_hashes.insert(item_hash, e);
        });
        let t_enc_local_elements_to_hashes = exec_time.elapsed();

        let mut remote_hashes = HashMap::new();
        let exec_time = Instant::now();
        remote.iter().cloned().for_each(|e| {
            let item_hash = hasher.hash_one(&e);
            remote_hashes.insert(item_hash, e);
        });
        let t_enc_remote_elements_to_hashes = exec_time.elapsed();

        let (
            local_only_hashes,
            remote_only_hashes,
            t_enc_local_sketch,
            t_enc_remote_sketch,
            t_dec_sketches,
        ) = if nr_diffs > 0 {
            let exec_time = Instant::now();
            let mut local_sketch =
                Minisketch::try_new(mem::size_of::<u64>() as u32 * 8, 0, nr_diffs).unwrap();
            for hash in local_hashes.keys().cloned() {
                local_sketch.add(hash);
            }
            let t_enc_local_sketch = exec_time.elapsed();

            let exec_time = Instant::now();
            let mut remote_sketch =
                Minisketch::try_new(mem::size_of::<u64>() as u32 * 8, 0, nr_diffs).unwrap();
            for hash in remote_hashes.keys().cloned() {
                remote_sketch.add(hash);
            }
            let t_enc_remote_sketch = exec_time.elapsed();

            // 3. Send Coded symbols until the remote replica has enough to decode all the differences
            let exec_time = Instant::now();
            let capacity = local_sketch.merge(&remote_sketch).unwrap();
            let mut diffs = vec![0u64; capacity];
            let _ = local_sketch.decode(&mut diffs).map_err(|_| ()).unwrap();
            let (local_only_hashes, remote_only_hashes): (Vec<_>, Vec<_>) = diffs
                .into_iter()
                .take(nr_diffs)
                .partition(|hash| local_hashes.contains_key(hash));
            let t_dec_sketches = exec_time.elapsed();
            (
                local_only_hashes,
                remote_only_hashes,
                t_enc_local_sketch,
                t_enc_remote_sketch,
                t_dec_sketches,
            )
        } else {
            (
                vec![],
                vec![],
                Duration::from_secs(0),
                Duration::from_secs(0),
                Duration::from_secs(0),
            )
        };

        tracker.increment_metadata(nr_diffs * mem::size_of::<u64>());

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
                .sum(),
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
            t_enc_local_elements_to_hashes
                + t_enc_remote_elements_to_hashes
                + t_enc_local_sketch
                + t_enc_remote_sketch,
        );

        tracker.increment_t_dec(
            t_dec_sketches + t_dec_local_hashes_to_elem + t_dec_remote_hashes_to_elem,
        );

        // 9. Sanity Check
        local.extend(remote_only_elements);
        remote.extend(local_only_elements);

        let local_set: HashSet<T> = local.into_iter().collect();
        let remote_set: HashSet<T> = remote.into_iter().collect();

        // Elements only in local_vec
        let local_only = local_set.difference(&remote_set);

        // Elements only in remote_vec
        let remote_only = remote_set.difference(&local_set);

        let false_matches = local_only.count() + remote_only.count();
        tracker.finish(false_matches);
    }
}
