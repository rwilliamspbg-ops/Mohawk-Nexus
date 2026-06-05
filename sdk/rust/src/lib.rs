use serde::{Deserialize, Serialize};

pub mod bridge_contract;

const ROUND6_FACTOR: f64 = 1_000_000.0;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FLState {
    pub round: i64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub global: Option<f64>,
    pub updates: Vec<f64>,
}

fn round6(v: f64) -> f64 {
    ((v * ROUND6_FACTOR + 0.5) as i64) as f64 / ROUND6_FACTOR
}

pub fn swip_scale(value: f64) -> f64 {
    round6(value * 1.5)
}

pub fn fl_apply_update(state: FLState, value: f64) -> FLState {
    let num_updates = state.updates.len() + 1;

    if num_updates >= 2 {
        let sum: f64 = state.updates.iter().copied().sum::<f64>() + value;
        let avg = round6(sum / num_updates as f64);
        return FLState {
            round: state.round + 1,
            global: Some(avg),
            updates: Vec::new(),
        };
    }

    FLState {
        round: state.round,
        global: None,
        updates: vec![round6(value)],
    }
}

#[cfg(test)]
mod benches {
    use super::*;
    use test::Bencher;

    #[bench]
    fn bench_swip_scale(b: &mut Bencher) {
        let value = 123.456789_f64;
        b.iter(|| swip_scale(value));
    }

    #[bench]
    fn bench_fl_apply_update_aggregate(b: &mut Bencher) {
        let state = FLState {
            round: 5,
            global: None,
            updates: vec![10.5, 20.3, 30.7],
        };
        let value = 40.2_f64;
        b.iter(|| fl_apply_update(state.clone(), value));
    }

    #[bench]
    fn bench_fl_apply_update_buffer(b: &mut Bencher) {
        let state = FLState {
            round: 0,
            global: None,
            updates: vec![],
        };
        let value = 15.75_f64;
        b.iter(|| fl_apply_update(state.clone(), value));
    }

    #[bench]
    fn bench_fl_apply_update_second_update(b: &mut Bencher) {
        let state = FLState {
            round: 1,
            global: None,
            updates: vec![25.5],
        };
        let value = 35.25_f64;
        b.iter(|| fl_apply_update(state.clone(), value));
    }
}
