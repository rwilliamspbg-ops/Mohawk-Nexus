# Contributing

Thanks for improving Mohawk Nexus.

## Development model

Mohawk Nexus is an integration workspace that aggregates multiple components:

- SMIP-MWP (Go control plane and integrations)
- SMIP-MWP-Rust (Rust datapath)
- Sovereign-Mohawk-Proto (protocol and verification assets)

This repository may track component snapshots while CI checks out authoritative upstream repos for integration jobs.

## Quick contributor flow

1. Create a branch from main.
2. Run setup and checks:
   - `make setup`
   - `make fmt-all`
   - `make lint`
   - `make test-all`
3. Update docs when behavior or interfaces change.
4. Open a PR with a clear summary and test evidence.

## Interface and contract changes

If you change bridge semantics:

1. Update files under bridge/.
2. Run `make generate-bridge`.
3. Run `make validate-bridge`.
4. Add or update examples in bridge/examples/.

## Component sync and pinning process

Use one of these approaches and document the chosen SHA(s) in your PR:

- Submodule strategy: pin each component submodule SHA and update recursively in CI.
- Snapshot strategy (current): keep component directories in sync with upstream commits and record source SHAs in PR notes.

When updating component references, include:

- Source repository and commit SHA
- Why the update is needed
- Any required migration steps

## Code style

- Follow .editorconfig defaults.
- Use pre-commit hooks when available.
- Keep changes scoped and avoid unrelated refactors.

## Commit and PR guidance

- Use focused commits with descriptive messages.
- Link relevant issues.
- Include benchmark or profiling data for datapath-sensitive changes.

## Security

Do not report vulnerabilities in public issues.
Use SECURITY.md for coordinated disclosure instructions.
