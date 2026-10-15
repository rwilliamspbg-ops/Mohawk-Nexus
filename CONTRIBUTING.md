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

The workspace tracks each component as a **gitlink** (a `160000` index entry)
rather than as a vendored snapshot, so the component sources live in their own
repositories and this repo records which commit of each it was verified against.

There is deliberately **no `.gitmodules`**: CI does not run
`git submodule update --init`. Every job that needs component sources checks
them out explicitly with `actions/checkout` at upstream `main`, which is why the
recorded SHAs are a provenance record rather than something the build consumes.
Keep them current anyway — a stale or unresolvable pin is misleading about what
was actually tested.

To refresh the recorded SHAs after merging component work:

```bash
for r in SMIP-MWP SMIP-MWP-Rust Sovereign-Mohawk-Proto; do
  git -C "$r" fetch origin main && git -C "$r" checkout --quiet origin/main
done
git add SMIP-MWP SMIP-MWP-Rust Sovereign-Mohawk-Proto
```

Then confirm each pinned commit is reachable in its upstream repository before
committing; a pin that no longer resolves tells a future reader nothing.

When updating component references, include:

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
