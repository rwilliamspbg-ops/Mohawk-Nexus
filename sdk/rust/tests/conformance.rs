use mohawk_sdk_rs::{fl_apply_update, swip_scale, FLState};
use serde_json::Value;

#[test]
fn conformance_cases() {
    let raw = std::fs::read_to_string("../fixtures/conformance/cases.json").expect("read fixture");
    let v: Value = serde_json::from_str(&raw).expect("parse fixture");
    let cases = v
        .get("cases")
        .and_then(|c| c.as_array())
        .expect("cases array");

    for case in cases {
        let name = case.get("name").and_then(|n| n.as_str()).unwrap_or("unnamed");
        let kind = case.get("kind").and_then(|k| k.as_str()).expect("kind");

        match kind {
            "swip_scale" => {
                let input = case
                    .get("input")
                    .and_then(|i| i.get("value"))
                    .and_then(|v| v.as_f64())
                    .expect("value");
                let expected = case
                    .get("expected")
                    .and_then(|e| e.get("result"))
                    .and_then(|v| v.as_f64())
                    .expect("result");
                let got = swip_scale(input);
                assert_eq!(got, expected, "{name}");
            }
            "fl_apply_update" => {
                let state_obj = case.get("input").and_then(|i| i.get("state")).expect("state");
                let round = state_obj.get("round").and_then(|r| r.as_i64()).expect("round");
                let updates = state_obj
                    .get("updates")
                    .and_then(|u| u.as_array())
                    .expect("updates")
                    .iter()
                    .map(|n| n.as_f64().expect("f64"))
                    .collect::<Vec<_>>();
                let value = case
                    .get("input")
                    .and_then(|i| i.get("value"))
                    .and_then(|v| v.as_f64())
                    .expect("value");

                let got = fl_apply_update(
                    FLState {
                        round,
                        global: None,
                        updates,
                    },
                    value,
                );

                let expected = case.get("expected").expect("expected");
                let expected_round = expected.get("round").and_then(|r| r.as_i64()).expect("round");
                assert_eq!(got.round, expected_round, "{name} round");

                if let Some(global) = expected.get("global") {
                    assert_eq!(got.global, Some(global.as_f64().expect("global")), "{name} global");
                }

                let expected_updates = expected
                    .get("updates")
                    .and_then(|u| u.as_array())
                    .map(|arr| {
                        arr.iter()
                            .map(|n| n.as_f64().expect("f64"))
                            .collect::<Vec<_>>()
                    })
                    .unwrap_or_default();
                assert_eq!(got.updates, expected_updates, "{name} updates");
            }
            _ => panic!("unknown case kind: {kind}"),
        }
    }
}

#[test]
fn bridge_contract_metadata() {
    let raw = std::fs::read_to_string("../../bridge/bridge_contract.version.json").expect("read version");
    let v: Value = serde_json::from_str(&raw).expect("parse version");

    assert_eq!(
        mohawk_sdk_rs::bridge_contract::BRIDGE_CONTRACT_NAME,
        v.get("contract").and_then(|x| x.as_str()).expect("contract")
    );
    assert_eq!(
        mohawk_sdk_rs::bridge_contract::BRIDGE_CONTRACT_SCHEMA_VERSION,
        v.get("schema_version")
            .and_then(|x| x.as_str())
            .expect("schema_version")
    );
    assert_eq!(
        mohawk_sdk_rs::bridge_contract::BRIDGE_CONTRACT_MANIFEST_VERSION,
        v.get("manifest_version")
            .and_then(|x| x.as_str())
            .expect("manifest_version")
    );
    assert_eq!(
        mohawk_sdk_rs::bridge_contract::BRIDGE_CONTRACT_SCHEMA_SHA256.len(),
        64
    );
}
