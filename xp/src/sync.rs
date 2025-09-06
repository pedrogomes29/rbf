use std::{
    hash::{Hash, RandomState},
    mem,
};

use crate::{
    bloom::BloomFilter,
    rateless_bloom::RatelessBF,
    riblt::{RatelessIBLT, Symbol},
    tracker::Telemetry,
};

pub mod bf_riblt;
pub mod pinsketch;
pub mod full_state_transfer;
pub mod rbf_riblt;
pub mod riblt;

pub trait Algorithm<T> {
    type Tracker: Telemetry;

    fn sync(&self, local: Vec<T>, remote: Vec<T>, tracker: &mut Self::Tracker);
}

pub trait Measure {
    fn size_of(item: &Self) -> usize;
}

impl Measure for String {
    fn size_of(item: &Self) -> usize {
        item.len()
    }
}

pub trait BuildFilter<T: Hash> {
    fn filter_from(&self, decompositions: &[T], fpr: f64) -> BloomFilter<T> {
        let mut filter = BloomFilter::new(decompositions.len(), fpr);
        decompositions.iter().for_each(|e| filter.timed_insert(e));

        filter
    }

    fn partition(&self, filter: &mut BloomFilter<T>, elements: Vec<T>) -> (Vec<T>, Vec<T>) {
        elements.into_iter().partition(|e| filter.timed_contains(e))
    }

    fn size_of(filter: &BloomFilter<T>) -> usize {
        filter.bitslice().chunks(8).count()
            + mem::size_of::<RandomState>() * 2
            + mem::size_of::<u64>()
    }
}

pub trait BuildRatelessIBLT<T>
where
    T: Symbol,
{
    fn riblt_from(&self, elements: &[T]) -> RatelessIBLT<T> {
        let mut riblt = RatelessIBLT::new();
        elements.iter().for_each(|symbol| {
            riblt.add_symbol(symbol.clone());
        });
        riblt
    }
}

pub trait BuildRatelessFilter<T>
where
    T: Hash,
{
    fn filter_from(&self, elements: Vec<T>, m_ratio: f64) -> RatelessBF<T> {
        let m = (elements.len() as f64 * m_ratio).ceil() as usize;
        let filter = RatelessBF::new(elements, m);
        filter
    }

    fn partition(&self, rateless_bf: &RatelessBF<T>, elements: Vec<T>) -> (Vec<T>, Vec<T>) {
        elements.into_iter().partition(|e| rateless_bf.contains(e))
    }
}
