use serde::{Deserialize, Serialize};

pub mod bridge_contract;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FLState {
    pub round: i64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub global: Option<f64>,
    pub updates: Vec<f64>,
}

fn round6(v: f64) -> f64 {
    (v * 1_000_000.0).round() / 1_000_000.0
}

pub fn swip_scale(value: f64) -> f64 {
    round6(value * 1.5)
}

pub fn fl_apply_update(state: FLState, value: f64) -> FLState {
    let mut updates = state.updates.clone();
    updates.push(value);

    if updates.len() >= 2 {
        let sum: f64 = updates.iter().copied().sum();
        let avg = round6(sum / updates.len() as f64);
        return FLState {
            round: state.round + 1,
            global: Some(avg),
            updates: vec![],
        };
    }

    FLState {
        round: state.round,
        global: None,
        updates: updates.into_iter().map(round6).collect(),
    }
}
