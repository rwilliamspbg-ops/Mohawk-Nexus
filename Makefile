SHELL := /usr/bin/env bash

.PHONY: bootstrap bridge-smoke verify validate-bridge generate-bridge verify-go verify-rust status
bootstrap:
	bash ./scripts/bootstrap.sh

bridge-smoke:
	bash ./scripts/bridge_smoke.sh

generate-bridge:
	python3 ./scripts/generate_bridge_contract.py

validate-bridge:
	go test ./SMIP-MWP/internal/bridge -run 'TestBridgeContractArtifacts|TestBridgeContractManifest|TestControlRequestMatchesFixture|TestControlRequestRoundTrip|TestTelemetryResponseMarshal'
	cd ./SMIP-MWP-Rust && . "$$HOME/.cargo/env" && cargo test -p cli bridge_contract_artifacts_round_trip
	cd ./SMIP-MWP-Rust && . "$$HOME/.cargo/env" && cargo test -p cli bridge_contract_manifest_matches_artifacts

verify-go:
	go test ./SMIP-MWP/... ./Sovereign-Mohawk-Proto/...

verify-rust:
	cd ./SMIP-MWP-Rust && . "$$HOME/.cargo/env" && cargo test --workspace --all-targets

verify:
	$(MAKE) generate-bridge
	$(MAKE) validate-bridge
	$(MAKE) verify-go
	$(MAKE) verify-rust
	bash ./scripts/bridge_smoke.sh

status:
	bash ./scripts/workspace_status.sh
