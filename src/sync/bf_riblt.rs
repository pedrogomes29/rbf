use std::{
    collections::{HashMap, HashSet},
    fmt::Display,
    hash::{BuildHasher, Hash, RandomState},
    marker::PhantomData,
    mem,
};

use crate::{
    riblt::RatelessIBLT, sync::Measure, tracker::{DefaultEvent, DefaultTracker, Telemetry}
};

use super::{Algorithm, BuildFilter};

#[derive(Clone, Copy, Debug)]
pub struct BloomRIBLT<T> {
    fpr: f64,
    _marker: PhantomData<T>,
}

impl<T> BloomRIBLT<T> {
    #[inline]
    #[must_use]
    pub fn new(fpr: f64) -> Self {
        assert!(
            fpr > 0.0 && (0.0..1.0).contains(&fpr),
            "fpr should be a ratio in the interval (0.0, 1.0)"
        );

        Self {
            fpr,
            _marker: PhantomData,
        }
    }
}

impl<T> Default for BloomRIBLT<T> {
    fn default() -> Self {
        Self {
            fpr: 0.01,
            _marker: PhantomData,
        }
    }
}

impl<T> Display for BloomRIBLT<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Bloom+Rateless[fpr={}%]", self.fpr * 100.0)
    }
}

impl<T: Hash> BuildFilter<T> for BloomRIBLT<T> {}

impl<T> Algorithm<T> for BloomRIBLT<T>
where
    T: Clone + Hash + Measure + Eq,
{
    type Tracker = DefaultTracker;

    fn sync(&self, mut local: Vec<T>, mut remote: Vec<T>, tracker: &mut Self::Tracker) {
        assert!(
            tracker.is_ready(),
            "tracker should be ready, i.e., no captured events and not finished"
        );
        const CODED_SYMBOL_SIZE: usize =
            mem::size_of::<u64>() + mem::size_of::<u64>() + mem::size_of::<i64>();

        let hasher = RandomState::new();

        // 1. Create a bloom filter from the local elements and send it to the remote replica.
        let local_filter = self.filter_from(&local, self.fpr);

        tracker.register(DefaultEvent::LocalToRemote {
            state: 0,
            metadata: <Self as BuildFilter<T>>::size_of(&local_filter),
            upload: tracker.upload(),
        });

        // 2. Partion the remote elements into *probably* present in both replicas or
        //    *definitely not* present in the local replica.
        let (remote_common, local_unknown) = self.partition(&local_filter, remote.clone());

        // 3. Build a bloom filter from the partion of *probably* common elements
        let remote_filter = self.filter_from(&remote_common, self.fpr);

        // 4. Calculate the hashes of the *probably* common elements and put them into the sketch
        //    to be streamed for synchronization
        let remote_hashes = {
            let mut remote_hashes = HashMap::new();
            remote_common.into_iter().for_each(|elem| {
                let elem_hash = hasher.hash_one(&elem);
                remote_hashes.insert(elem_hash, elem);
            });
            remote_hashes
        };
        let mut remote_iblt = RatelessIBLT::riblt_from(remote_hashes.keys().cloned());

        // 5. Partion the local elements into *probably* present in both replicas or
        //    *definitely not* present in the remote replica. (same as 2)
        let (local_common, remote_unknown) = self.partition(&remote_filter, local.clone());

        // 6. Calculate the hashes of the *probably* common elements and put them into the sketch
        //    to be streamed for synchronization (same as 4)
        let local_hashes = {
            let mut local_hashes = HashMap::new();
            local_common.into_iter().for_each(|elem| {
                let elem_hash = hasher.hash_one(&elem);
                local_hashes.insert(elem_hash, elem);
            });
            local_hashes
        };
        let mut local_iblt = RatelessIBLT::riblt_from(local_hashes.keys().cloned());

        local_iblt.find_all_differences(&mut remote_iblt);

        let sketch_size = local_iblt.sketch.len();
        assert_eq!(sketch_size, remote_iblt.sketch.len());

        //message with just received filter + sketch
        tracker.register(DefaultEvent::RemoteToLocal {
            state: local_unknown.iter().map(<T as Measure>::size_of).sum(),
            metadata: <Self as BuildFilter<T>>::size_of(&remote_filter)
                + sketch_size * CODED_SYMBOL_SIZE,
            download: tracker.download(),
        });

        let local_only_hashes_fp = local_iblt.get_local_only_symbols();
        let remote_only_hashes_fp = local_iblt.get_remote_only_symbols();

        let local_only_elements_fp: Vec<_> = local_only_hashes_fp
            .into_iter()
            .map(|hash| local_hashes[&hash].clone())
            .collect();

        // 7. Send remote unknown state detected using the BF
        //    Send local only state due to false positives
        //    Send remote only hashes to request for remote only state due to false positives

        tracker.register(DefaultEvent::LocalToRemote {
            state: remote_unknown
                .iter()
                .chain(&local_only_elements_fp)
                .map(T::size_of)
                .sum(),
            metadata: remote_only_hashes_fp.len() * mem::size_of::<u64>(),
            upload: tracker.upload(),
        });

        let remote_only_elements_fp: Vec<_> = remote_only_hashes_fp
            .into_iter()
            .map(|hash| remote_hashes[&hash].clone())
            .collect();

        // 8. Send remote only state due to false positives
        tracker.register(DefaultEvent::RemoteToLocal {
            state: remote_only_elements_fp
                .iter()
                .map(<T as Measure>::size_of)
                .sum(),
            metadata: 0,
            download: tracker.download(),
        });


        remote.extend( remote_unknown);
        remote.extend( local_only_elements_fp);

        local.extend( local_unknown);
        local.extend( remote_only_elements_fp);


        let local_set: HashSet<T> = local.into_iter().collect();
        let remote_set: HashSet<T> = remote.into_iter().collect();

        // Elements only in local_vec
        let local_only = local_set
            .difference(&remote_set);

        // Elements only in remote_vec
        let remote_only = remote_set
            .difference(&local_set);

        let false_matches = local_only.count() + remote_only.count();
        // 9. Sanity check
        tracker.finish(false_matches);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{tracker::Bandwidth};

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

        let (download, upload) = (Bandwidth::Kbps(0.5), Bandwidth::Kbps(0.5));
        let mut tracker = DefaultTracker::new(download, upload);
        let bloom_buckets = BloomRIBLT::new(0.01);

        bloom_buckets.sync(local, remote, &mut tracker);
        assert_eq!(tracker.false_matches(), 0);

        let events = tracker.events();
        assert_eq!(events.len(), 4);
    }
}
