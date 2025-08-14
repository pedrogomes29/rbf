use std::{
    cmp::{max, min}, collections::HashSet, hash::Hash
};

use rand::{seq::SliceRandom, SeedableRng};

use crate::bayesian_estimation;

use super::{RatelessBF, StoppingStrategy, StoppingStrategyFactory};

const CONFIDENCE_LEVEL: f64 = 0.95;

pub struct BayesianSimilarity<T: Hash> {
    receiver_bf: RatelessBF<T>,
    sampled_positives: Vec<T>,
    sampled_negatives: Vec<T>,
    not_chosen_elements: Vec<T>,
    alpha: usize,
    beta: usize,
    target_similarity: f64,
}

impl<T: Hash + Clone> BayesianSimilarity<T> {
    pub fn new(receiver_data: Vec<T>, target_similarity: f64, m_ratio: f64, not_chosen_elements: Vec<T>) -> Self {
        let m = (receiver_data.len() as f64 * m_ratio).ceil() as usize;
        let positives = receiver_data.clone();
        let receiver_bf = RatelessBF::new(receiver_data, m);
        Self {
            receiver_bf,
            sampled_positives: positives,
            sampled_negatives: vec![],
            not_chosen_elements,
            alpha: 1,
            beta: 1,
            target_similarity,
        }
    }
}

pub struct BayesianSimilarityFactory {
    pub m_ratio: f64,
    pub target_similarity: f64,
}

impl BayesianSimilarityFactory {
    pub fn new(m_ratio: f64, target_similarity: f64) -> Self {
        Self {
            target_similarity,
            m_ratio,
        }
    }
}

impl<T: Hash + Clone + Eq> StoppingStrategyFactory<T> for BayesianSimilarityFactory {
    type Strategy = BayesianSimilarity<T>;

    fn create(&self, elements: Vec<T>, sample_size: usize) -> Self::Strategy {
        let mut rng: rand::prelude::StdRng = rand::rngs::StdRng::seed_from_u64(42);

        let sampled_elements: Vec<_> = elements
            .choose_multiple(&mut rng, sample_size)
            .cloned()
            .collect();

        let sampled_elements_set: HashSet<_> = sampled_elements.iter().collect();

        let not_chosen_elements: Vec<_> = elements
            .into_iter()
            .filter(|e| !sampled_elements_set.contains(e))
            .collect();


        BayesianSimilarity::new(sampled_elements, self.target_similarity, self.m_ratio, not_chosen_elements)
    }

    fn print_name(&self) -> String {
        "Similarity".to_string()
    }

    fn print_params(&self) -> String {
        format!("sim={}", self.target_similarity)
    }
}

impl<T: Hash + Clone> StoppingStrategy<T> for BayesianSimilarity<T> {
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
        
        let desired_intersection = ((self.target_similarity * self.receiver_bf.data.len() as f64)
            - true_negatives as f64)
            .round() as i32;

        const SMALL_FILTER_MAX_SIZE: usize = 2500;

        let confidence = if sender_bf.data.len() < SMALL_FILTER_MAX_SIZE {
            let n_receiver = self.receiver_bf.data.len();
            bayesian_estimation::numeric_posterior_tail(
                self.alpha,
                self.alpha + self.beta,
                sender_bf.data.len(),
                self.receiver_bf.data.len(),
                self.receiver_bf.m,
                max(desired_intersection, 0) as usize,
                min(sender_bf.data.len(), n_receiver),
            )
        } else {
            bayesian_estimation::probability_converged_beta_tail(
                self.alpha as f64,
                self.beta as f64,
                desired_intersection,
                self.receiver_bf.data.len() as i32,
                sender_bf.data.len() as i32,
                self.receiver_bf.m as i32,
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
