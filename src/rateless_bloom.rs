use super::bloom::BloomFilter;
use std::{
    cmp::max, error::Error, fmt::{self, Display, Formatter}, hash::{Hash, RandomState}, mem
};
use statrs::distribution::{Beta, ContinuousCDF};

pub mod angle_heuristic;
pub mod bayesian_similarity;
pub mod bayesian_no_params;

pub trait StoppingStrategyFactory<T: Hash> {
    type Strategy: StoppingStrategy<T>;
    fn create(&self, elements: Vec<T>, sample_size:usize) -> Self::Strategy;
    fn print_name(&self) -> String;
    fn print_params(&self) -> String;
}

pub trait StoppingStrategy<T: Hash> {
    fn on_extend(&mut self, bf: &RatelessBF<T>);
    fn should_stop(&mut self, bf: &RatelessBF<T>) -> bool;
}

#[derive(Debug)]
struct ConvergenceError(String);

impl Display for ConvergenceError {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl Error for ConvergenceError {}

pub struct RatelessBF<T: Hash> {
    bloom_filters: Vec<BloomFilter<T>>,
    data: Vec<T>,
    m: usize,
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
            m: max(m,1),
        }
    }

    pub fn extend(&mut self) {
        let mut filter = BloomFilter::from_raw_parts(self.m, 1);
        self.data.iter().for_each(|d| filter.insert(d));
        self.bloom_filters.push(filter);
    }

    pub fn extend_with_hashers(&mut self, hashers: [RandomState; 2]){
        let mut filter = BloomFilter::from_raw_parts_with_hashers(self.m, 1, hashers);
        self.data.iter().for_each(|d| filter.insert(d));
        self.bloom_filters.push(filter);
    }

    pub fn contains(&self, value: &T) -> bool {
        self.bloom_filters
            .iter()
            .all(|filter| filter.contains(value))
    }

    pub fn extend_until<S: StoppingStrategy<T>>(
        &mut self,
        mut strategy: S,
    ){
        let mut run = 1;
        loop{
            self.extend();
            strategy.on_extend(self);
            if strategy.should_stop(self) {
                //eprintln!("Coverged after {run} runs");
                return;
            }
            run+=1;
        }
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
}