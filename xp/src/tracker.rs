use std::time::Duration;

pub trait Telemetry {
    fn is_ready(&self) -> bool;
    fn state(&self) -> usize;
    fn metadata(&self) -> usize;
    fn bytes(&self) -> usize;
    fn t_enc(&self) -> Duration;
    fn t_dec(&self) -> Duration;
    fn increment_state(&mut self, additional_state:usize);
    fn increment_metadata(&mut self, additional_metadata:usize);
    fn increment_t_enc(&mut self, additional_t_enc: Duration);
    fn increment_t_dec(&mut self, additional_t_dec: Duration);
    fn finish(&mut self, false_matches: usize);
    fn false_matches(&self) -> usize;
}

#[derive(Debug)]
pub struct DefaultTracker {
    state: usize,
    metadata: usize,
    t_enc: Duration,
    t_dec: Duration,
    diffs: Option<usize>
}

impl DefaultTracker {
    #[inline]
    #[must_use]
    pub fn new() -> Self {
        Self {
            state: 0,
            metadata: 0,
            t_enc: Duration::from_secs(0),
            t_dec: Duration::from_secs(0),
            diffs: None,
        }
    }
}

impl Telemetry for DefaultTracker {
    fn is_ready(&self) -> bool {
        self.diffs.is_none()
    }

    fn state(&self) -> usize {
        self.state
    }
    fn metadata(&self) -> usize {
        self.metadata
    }
    fn bytes(&self) -> usize {
        self.metadata + self.state
    }
    fn t_enc(&self) -> Duration {
        self.t_enc
    }
    fn t_dec(&self) -> Duration {
        self.t_dec
    }

    fn increment_state(&mut self, additional_state:usize){
        self.state += additional_state
    }
    fn increment_metadata(&mut self, additional_metadata:usize){
        self.metadata += additional_metadata
    }
    fn increment_t_enc(&mut self, additional_t_enc: Duration) {
        self.t_enc += additional_t_enc
    }
    fn increment_t_dec(&mut self, additional_t_dec: Duration) {
        self.t_dec += additional_t_dec
    }

    fn finish(&mut self, diffs: usize) {
        if self.diffs.is_none() {
            self.diffs = Some(diffs)
        }
    }

    fn false_matches(&self) -> usize {
        self.diffs
            .expect("`finish()` should be called before `diffs()`")
    }
}
