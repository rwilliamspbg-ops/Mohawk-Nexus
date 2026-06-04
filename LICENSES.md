# Licensing Matrix

Mohawk-Nexus is a multi-repository integration workspace. Licensing is governed per component repository.

## Component Licenses

| Component | Repository | License (upstream) | Evidence |
|---|---|---|---|
| SMIP-MWP | `rwilliamspbg-ops/SMIP-MWP` | GNU Affero General Public License v3.0 (AGPL-3.0) | `LICENSE` header in upstream repo (AGPLv3 text) |
| SMIP-MWP-Rust | `rwilliamspbg-ops/SMIP-MWP-Rust` | GNU Affero General Public License v3.0 (AGPL-3.0) | `LICENSE` header in upstream repo (AGPLv3 text) |
| Sovereign-Mohawk-Proto | `rwilliamspbg-ops/Sovereign-Mohawk-Proto` | Apache License 2.0 | GitHub API repo license metadata (`Apache-2.0`) |
| Mohawk-Nexus root integration assets | `rwilliamspbg-ops/Mohawk-Nexus` | Mixed / derivative of component licenses as applicable | This workspace aggregates components and cross-repo integration files |

## How To Interpret This

1. Treat each component directory and imported source according to its upstream license.
2. For integration-only root files in this workspace, verify provenance before reuse if they incorporate component code or contract artifacts.
3. When redistributing a build or bundle, include all applicable upstream license texts and notices.

## Source Of Truth

- SMIP-MWP license text: `https://github.com/rwilliamspbg-ops/SMIP-MWP/blob/main/LICENSE`
- SMIP-MWP-Rust license text: `https://github.com/rwilliamspbg-ops/SMIP-MWP-Rust/blob/main/LICENSE`
- Sovereign-Mohawk-Proto license text: `https://github.com/rwilliamspbg-ops/Sovereign-Mohawk-Proto/blob/main/LICENSE`

If upstream license files change, this matrix must be updated in the same PR that updates component references.
