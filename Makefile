SHELL := /usr/bin/env bash

.PHONY: setup bootstrap bridge-smoke verify validate-bridge generate-bridge generate-bridge-bindings verify-go verify-rust status lint fmt-all test-all verify-generated e2e-bridge-portable e2e-bridge-accelerated hardening-check policy-apply-kyverno policy-apply-gatekeeper policy-validate policy-validate-strict

setup: bootstrap

bootstrap:
	bash ./scripts/bootstrap.sh

bridge-smoke:
	bash ./scripts/bridge_smoke.sh

generate-bridge:
	python3 ./scripts/generate_bridge_contract.py
	python3 ./scripts/generate_bridge_bindings.py

generate-bridge-bindings:
	python3 ./scripts/generate_bridge_bindings.py

validate-bridge:
	python3 ./scripts/generate_bridge_contract.py
	python3 ./scripts/validate_bridge_contract.py

verify-go:
	@pkgs="$$(go list ./SMIP-MWP/... ./Sovereign-Mohawk-Proto/... | grep -v 'github.com/rwilliamspbg-ops/Sovereign-Mohawk-Proto/internal/federation$$')"; \
	go test $$pkgs; \
	go test ./Sovereign-Mohawk-Proto/internal/federation -run '^$$'

verify-rust:
	cd ./SMIP-MWP-Rust && . "$$HOME/.cargo/env" && cargo test --workspace --all-targets

lint:
	python3 -m py_compile ./scripts/*.py ./fl/*.py ./swip/*.py ./tests/*.py
	go test ./SMIP-MWP/... ./Sovereign-Mohawk-Proto/... -run '^$$'
	cd ./sdk/rust && cargo check --all-targets --all-features
	cd ./sdk/typescript && npm install && if npm run | grep -q ' lint'; then npm run -s lint; else echo 'No lint script in sdk/typescript/package.json; skipping'; fi

fmt-all:
	python3 -m pip install --quiet black
	python3 -m black ./scripts ./fl ./swip ./tests ./sdk/python
	cd ./sdk/rust && cargo fmt --all
	cd ./sdk/typescript && npm install && if npm run | grep -q ' format'; then npm run -s format; else echo 'No format script in sdk/typescript/package.json; skipping'; fi

test-all:
	bash ./scripts/test_all_sdks.sh

e2e-bridge-portable:
	bash ./scripts/e2e_bridge_k8s.sh portable

e2e-bridge-accelerated:
	bash ./scripts/check_afxdp_prereqs.sh --require
	bash ./scripts/e2e_bridge_k8s.sh accelerated

hardening-check:
	bash ./scripts/check_k8s_runtime_hardening.sh accelerated

policy-apply-kyverno:
	kubectl apply -f ./k8s/policy/kyverno/mohawk-runtime-hardening.yaml

policy-apply-gatekeeper:
	kubectl apply -f ./k8s/policy/gatekeeper/template-mohawk-runtime-hardening.yaml
	kubectl apply -f ./k8s/policy/gatekeeper/constraint-mohawk-runtime-hardening.yaml

policy-validate:
	bash ./scripts/validate_admission_policies.sh

policy-validate-strict:
	bash ./scripts/validate_admission_policies.sh --require-present

verify-generated:
	git diff --exit-code -- bridge/ sdk/go/mohawksdk/bridge_contract.go sdk/rust/src/bridge_contract.rs sdk/python/mohawk_sdk/bridge_contract.py sdk/typescript/src/bridgeContract.js

verify:
	$(MAKE) generate-bridge
	$(MAKE) validate-bridge
	$(MAKE) verify-go
	bash ./scripts/bridge_smoke.sh

status:
	bash ./scripts/workspace_status.sh
