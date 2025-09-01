use super::bloom::BloomFilter;
use std::{
    cmp::max,
    hash::{Hash, RandomState},
    mem,
    time::{Duration, Instant},
};

pub mod angle_heuristic;
pub mod bayesian_cost;
pub mod bayesian_similarity;
pub mod expected_cost;

pub trait StoppingStrategyFactory<T: Hash> {
    type Strategy: StoppingStrategy<T>;
    fn create(&self, elements: Vec<T>, sample_size: usize) -> Self::Strategy;
    fn print_name(&self) -> String;
    fn print_params(&self) -> String;
}

pub trait StoppingStrategy<T: Hash> {
    fn on_extend(&mut self, bf: &mut RatelessBF<T>);
    fn should_stop(&mut self, bf: &mut RatelessBF<T>) -> Option<(Vec<T>, Vec<T>)>;
}

pub struct RatelessBF<T: Hash> {
    bloom_filters: Vec<BloomFilter<T>>,
    data: Vec<T>,
    m: usize,
    t_enc: Duration,
    t_dec: Duration,
}

impl<T> RatelessBF<T>
where
    T: Hash,
{
    #[inline]
    #[must_use]
    pub fn new(data: Vec<T>, m: usize) -> Self {
        Self {
            bloom_filters: Vec::new(),
            data,
            m: max(m, 1),
            t_enc: Duration::from_secs(0),
            t_dec: Duration::from_secs(0),
        }
    }

    pub fn extend(&mut self) {
        let mut filter = BloomFilter::from_raw_parts(self.m, 1);
        self.data.iter().for_each(|d| filter.insert(d));
        self.bloom_filters.push(filter);
    }

    pub fn extend_with_hashers(&mut self, hashers: [RandomState; 2]) {
        let mut filter = BloomFilter::from_raw_parts_with_hashers(self.m, 1, hashers);
        self.data.iter().for_each(|d| filter.insert(d));
        self.bloom_filters.push(filter);
    }

    pub fn contains(&self, value: &T) -> bool {
        self.bloom_filters
            .iter()
            .all(|filter| filter.contains(value))
    }

    pub fn extend_until<S: StoppingStrategy<T>>(&mut self, mut strategy: S) -> (Vec<T>, Vec<T>) {
        let mut _run = 1;
        loop {
            let exec_time = Instant::now();
            self.extend();
            self.t_enc += exec_time.elapsed();
            let exec_time = Instant::now();
            strategy.on_extend(self);
            if let Some(partitioned_elements) = strategy.should_stop(self) {
                self.t_dec += exec_time.elapsed();
                //eprintln!("Coverged after {run} runs");
                return partitioned_elements;
            }
            self.t_dec += exec_time.elapsed();
            _run += 1;
        }
    }

    pub fn on_extend<S: StoppingStrategy<T>>(&mut self, mut strategy: S) {
        strategy.on_extend(self);
    }

    pub fn size_of(&self) -> usize {
        if self.bloom_filters.is_empty() {
            return 0;
        }

        let standalone_bf = &self.bloom_filters[0];
        let standalone_bf_size = standalone_bf.bitslice().chunks(8).count();

        self.bloom_filters.len() * standalone_bf_size //combined bitarray size in Bytes
        + mem::size_of::<u64>() //size to transmit m the number of bits (in each of the internal BFs)
    }

    #[inline]
    pub fn t_enc(&self) -> Duration {
        self.t_enc
    }

    #[inline]
    pub fn t_dec(&self) -> Duration {
        self.t_dec
    }
}
