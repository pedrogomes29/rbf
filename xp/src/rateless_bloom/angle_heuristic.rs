use super::{RatelessBF, StoppingStrategy, StoppingStrategyFactory};
use std::{collections::VecDeque, f64::consts::PI, hash::Hash};

pub struct AngleHeuristic<T> {
    positives: Vec<T>,
    negatives: Vec<T>,
    angle_threshold_deg: f64,
    window_size: usize,
    recent_angles: VecDeque<f64>,
    last_normalized: Option<f64>,
}

impl<T: Hash> AngleHeuristic<T> {
    pub fn new(elements: Vec<T>, angle_threshold_deg: f64, window_size: usize) -> Self {
        Self {
            positives: elements,
            negatives: vec![],
            angle_threshold_deg,
            window_size,
            recent_angles: VecDeque::with_capacity(window_size),
            last_normalized: None,
        }
    }
}

pub struct AngleHeuristicFactory {
    angle_threshold_deg: f64,
    window_size: usize,
}

impl AngleHeuristicFactory {
    pub fn new(angle_threshold_deg: f64, window_size: usize) -> Self {
        Self {
            angle_threshold_deg,
            window_size,
        }
    }
}

impl<T: Hash + Clone> StoppingStrategyFactory<T> for AngleHeuristicFactory {
    type Strategy = AngleHeuristic<T>;

    fn create(&self, elements: Vec<T>, _sample_size: usize) -> Self::Strategy {
        AngleHeuristic::new(elements, self.angle_threshold_deg, self.window_size)
    }

    fn print_name(&self) -> String {
        "Heuristic".to_string()
    }

    fn print_params(&self) -> String {
        format!("angle={}", self.angle_threshold_deg)
    }
}

impl<T: Hash + Clone> StoppingStrategy<T> for AngleHeuristic<T> {
    fn on_extend(&mut self, bf: &mut RatelessBF<T>) {
        let sender_last_slice = bf.bloom_filters.last().unwrap();

        let new_negatives: Vec<_>;
        (self.positives, new_negatives) =
            self.positives.drain(..).partition(|e| sender_last_slice.contains(e));
            
        self.negatives.extend(new_negatives);
            
        let normalized = self.positives.len() as f64 / (self.positives.len() + self.negatives.len()).max(1) as f64;

        if let Some(prev) = self.last_normalized {
            let dy = normalized - prev;
            let angle = dy.abs().atan() * 180.0 / PI;

            if self.recent_angles.len() == self.window_size {
                self.recent_angles.pop_front();
            }
            self.recent_angles.push_back(angle);
        }

        self.last_normalized = Some(normalized);
    }

    fn should_stop(&mut self, _: &mut RatelessBF<T>) -> Option<(Vec<T>, Vec<T>)> {
        if self.recent_angles.len() < self.window_size {
            return None;
        }
        let avg: f64 = self.recent_angles.iter().sum::<f64>() / self.window_size as f64;
        if avg >= self.angle_threshold_deg{
            return None;
        }

        return Some((self.positives.clone(), self.negatives.clone()));
    }
}
