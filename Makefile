SHELL := /usr/bin/env bash

.PHONY: bootstrap bridge-smoke verify validate-bridge generate-bridge verify-go verify-rust status
bootstrap:
	bash ./scripts/bootstrap.sh

bridge-smoke:
	bash ./scripts/bridge_smoke.sh

generate-bridge:
	python3 ./scripts/generate_bridge_contract.py

validate-bridge:
	python3 ./scripts/generate_bridge_contract.py
	python3 ./scripts/validate_bridge_contract.py

verify-go:
	go test ./SMIP-MWP/... ./Sovereign-Mohawk-Proto/...

verify-rust:
	cd ./SMIP-MWP-Rust && . "$$HOME/.cargo/env" && cargo test --workspace --all-targets

verify:
	$(MAKE) generate-bridge
	$(MAKE) validate-bridge
	$(MAKE) verify-go
	bash ./scripts/bridge_smoke.sh

status:
	bash ./scripts/workspace_status.sh
