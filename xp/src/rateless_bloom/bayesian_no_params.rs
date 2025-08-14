use crate::bayesian_estimation;
use rand::{SeedableRng, seq::SliceRandom};
use std::{
    cmp::{max, min},
    hash::Hash,
    collections::HashSet,
};

use super::{RatelessBF, StoppingStrategy, StoppingStrategyFactory};

const HASH_SIZE: usize = std::mem::size_of::<u64>();
const SYMBOL_SIZE: usize = HASH_SIZE;
const COUNTER_SIZE: usize = std::mem::size_of::<u64>();
const IBLT_SYMBOL_SIZE: usize = SYMBOL_SIZE + HASH_SIZE + COUNTER_SIZE;
const CONFIDENCE_LEVEL: f64 = 0.95;

const fn round_mul(multiplier_millis: usize, value: usize) -> usize {
    (multiplier_millis * value + 500) / 1000
}

const RATELESS_SET_RECONCILIATION_MULTIPLIER_MILLIS: usize = 1350;
const RATELESS_SET_RECONCILIATION_OVERHEAD: usize = HASH_SIZE
    + round_mul(
        RATELESS_SET_RECONCILIATION_MULTIPLIER_MILLIS,
        IBLT_SYMBOL_SIZE,
    );

pub struct BayesianNoParams<T: Hash> {
    receiver_bf: RatelessBF<T>,
    sampled_positives: Vec<T>,
    sampled_negatives: Vec<T>,
    not_chosen_elements: Vec<T>,
    alpha: usize,
    beta: usize,
}

impl<T: Hash + Clone> BayesianNoParams<T> {
    pub fn new(receiver_data: Vec<T>, m_ratio: f64, not_chosen_elements: Vec<T>) -> Self {
        let m = (receiver_data.len() as f64 * m_ratio).ceil() as usize;
        let positives = receiver_data.clone();
        let receiver_bf = RatelessBF::new(receiver_data, m);
        Self {
            receiver_bf,
            not_chosen_elements,
            sampled_positives: positives,
            sampled_negatives: vec![],
            alpha: 1,
            beta: 1,
        }
    }
}

pub struct BayesianNoParamsFactory {
    pub m_ratio: f64,
}

impl BayesianNoParamsFactory {
    pub fn new(m_ratio: f64) -> Self {
        Self { m_ratio }
    }
}

impl<T: Hash + Clone + Eq> StoppingStrategyFactory<T> for BayesianNoParamsFactory {
    type Strategy = BayesianNoParams<T>;

    fn create(&self, elements: Vec<T>, sample_size: usize) -> Self::Strategy {
        let mut rng = rand::rngs::StdRng::seed_from_u64(42);

        let sampled_elements: Vec<_> = elements
            .choose_multiple(&mut rng, sample_size)
            .cloned()
            .collect();

        let sampled_elements_set: HashSet<_> = sampled_elements.iter().collect();

        let not_chosen_elements: Vec<_> = elements
            .into_iter()
            .filter(|e| !sampled_elements_set.contains(e))
            .collect();


        BayesianNoParams::new(sampled_elements, self.m_ratio, not_chosen_elements)
    }

    fn print_name(&self) -> String {
        "NoParams".to_string()
    }

    fn print_params(&self) -> String {
        "".to_string()
    }
}

impl<T: Hash + Clone + Eq> StoppingStrategy<T> for BayesianNoParams<T> {
    fn on_extend(&mut self, sender_bf: &mut RatelessBF<T>) {
        let sender_last_slice = sender_bf.bloom_filters.last().unwrap();
        self.receiver_bf
            .extend_with_hashers(sender_last_slice.hashers());

        let receiver_last_slice = self.receiver_bf.bloom_filters.last().unwrap();
        let mut tmp = sender_last_slice.bitslice().to_bitvec();
        tmp &= receiver_last_slice.bitslice();

        let new_negatives: Vec<_>;
        (self.sampled_positives, new_negatives) =
            self.sampled_positives.drain(..).partition(|e| sender_last_slice.contains(e));
        self.sampled_negatives.extend(new_negatives);


        let and_ones = tmp.count_ones();
        self.alpha += and_ones;
        self.beta += sender_bf.m - and_ones;
    }

    fn should_stop(&mut self, sender_bf: &mut RatelessBF<T>) -> Option<(Vec<T>, Vec<T>)> {
        let true_negatives = self.sampled_negatives.len() as i32;
        let n_sender = sender_bf.data.len() as i32;
        let m = sender_bf.m;
        let m_bytes = m / 8;
        let fpr = 1.0 - (1.0 - 1.0 / m as f64).powi(n_sender);
        let sample_size = self.receiver_bf.data.len();

        let original_set_size = self.not_chosen_elements.len() + self.receiver_bf.data.len();

        let _sample_size_offset = original_set_size as f64 / sample_size as f64;
        let sample_size_offset = 1.0;

        let desired_new_negatives =
            m_bytes as f64 / (RATELESS_SET_RECONCILIATION_OVERHEAD as f64 / sample_size_offset);

        let desired_false_positives = (desired_new_negatives / (1.0 - fpr)).round() as i32;

        let desired_intersection = n_sender - true_negatives - desired_false_positives;

        let confidence = {
            let n_receiver = self.receiver_bf.data.len();
            bayesian_estimation::numeric_posterior_tail(
                self.alpha,
                self.alpha + self.beta,
                n_sender.try_into().unwrap(),
                n_receiver,
                m,
                max(desired_intersection, 0) as usize,
                min(n_sender as usize, n_receiver),
            )
        };
        
        if confidence <= CONFIDENCE_LEVEL{
            return None;
        }

        let (mut positives, mut negatives): (Vec<_>, Vec<_>) = 
            self.not_chosen_elements.drain(..).partition(|e| sender_bf.contains(e));

        positives.extend(self.sampled_positives.clone());
        negatives.extend(self.sampled_negatives.clone());

        return Some((positives, negatives));
    }
}
