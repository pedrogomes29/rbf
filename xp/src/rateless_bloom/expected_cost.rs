use super::{RatelessBF, StoppingStrategy, StoppingStrategyFactory};
use std::hash::Hash;
use crate::rateless_bloom::bayesian_cost::RATELESS_SET_RECONCILIATION_OVERHEAD;

pub struct ExpectedCost<T> {
    positives: Vec<T>,
    negatives: Vec<T>,
    new_negatives: Option<usize>,
    m: usize,
}

impl<T: Hash> ExpectedCost<T> {
    pub fn new(elements: Vec<T>, m: usize) -> Self {
        Self {
            positives: elements,
            negatives: vec![],
            new_negatives: None,
            m
        }
    }

    /// We stop when it becomes more efficient to use rateless set reconciliation
    /// than to continue with the Bloom filter. The threshold is calculated based on
    /// the number of elements that could be recovered with rateless set reconciliation
    /// using the m bits from the Bloom filter.
    fn get_reconciliation_threshold(&self) -> usize {
        self.m / (RATELESS_SET_RECONCILIATION_OVERHEAD * 8) 
        //times 8 because the reconciliation overhead is in bytes, while m is in bits
    }
}

pub struct ExpectedCostFactory {
    m_ratio: f64
}

impl ExpectedCostFactory {
    pub fn new(m_ratio: f64) -> Self {
        Self { m_ratio }
    }
}

impl<T: Hash + Clone> StoppingStrategyFactory<T> for ExpectedCostFactory {
    type Strategy = ExpectedCost<T>;

    fn create(&self, elements: Vec<T>, _sample_size: usize) -> Self::Strategy {
        let m = (elements.len() as f64 * self.m_ratio).ceil() as usize;
        ExpectedCost::new(elements, m)
    }

    fn print_name(&self) -> String {
        "ExpectedCost".to_string()
    }

    fn print_params(&self) -> String {
        "".to_string()
    }
}

impl<T: Hash + Clone> StoppingStrategy<T> for ExpectedCost<T> {
    fn on_extend(&mut self, bf: &mut RatelessBF<T>) {
        let sender_last_slice = bf.bloom_filters.last().unwrap();

        let new_negatives: Vec<_>;
        (self.positives, new_negatives) =
            self.positives.drain(..).partition(|e| sender_last_slice.contains(e));
            
        self.new_negatives = Some(new_negatives.len());
        self.negatives.extend(new_negatives);
    }

    fn should_stop(&mut self, _: &mut RatelessBF<T>) -> Option<(Vec<T>, Vec<T>)> {
        if let Some(new_negatives) = self.new_negatives {
            let threshold = self.get_reconciliation_threshold();
            if new_negatives >= threshold {
                return None;
            }
            return Some((self.positives.clone(), self.negatives.clone()));
        }
        None
    }
}
