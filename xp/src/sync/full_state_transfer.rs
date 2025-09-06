use crate::{
    sync::{Algorithm, Measure},
    tracker::{DefaultTracker, Telemetry},
};
use std::{
    collections::HashSet,
    fmt::Display,
    hash::Hash,
    marker::PhantomData,
};

pub struct FullStateTransfer<T> {
    _marker: PhantomData<T>,
}

impl<T> FullStateTransfer<T> {
    #[inline]
    #[must_use]
    pub fn new() -> Self {
        Self {
            _marker: PhantomData,
        }
    }
}

impl<T> Display for FullStateTransfer<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "FullStateTransfer")
    }
}

impl<T> Algorithm<T> for FullStateTransfer<T>
where
    T: Clone + Hash + Measure + Eq,
{
    type Tracker = DefaultTracker;

    // This sync method simulates a full state exchange where the local set is sent first,
    // and the remote sends back only the missing elements.
    fn sync(&self, mut local: Vec<T>, mut remote: Vec<T>, tracker: &mut Self::Tracker) {
        // 1. Simulate transferring the entire local set to the remote.
        tracker.increment_state(local.iter().map(|element| T::size_of(element)).sum());

        // 2. Simulate the remote calculating the elements it's missing.
        let local_set: HashSet<_> = local.iter().collect();
        let remote_set: HashSet<_> = remote.iter().collect();

        // Identify the elements that are in the remote set but not in the local set.
        let remote_only_elements: Vec<T> = remote_set
            .difference(&local_set)
            .map(|&element| element.clone())
            .collect();
        
        // 3. Simulate the remote sending its unique elements to the local.
        tracker.increment_state(remote_only_elements.iter().map(|element| T::size_of(element)).sum());
            
        // Sanity check to ensure synchronization is complete.
        remote.extend(local.clone());
        local.extend(remote_only_elements);

        let final_local_set: HashSet<T> = local.into_iter().collect();
        let final_remote_set: HashSet<T> = remote.into_iter().collect();

        let false_matches = final_local_set.difference(&final_remote_set).count()
            + final_remote_set.difference(&final_local_set).count();
        tracker.finish(false_matches);
    }
}
