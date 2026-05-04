# Contributing to Mohawk Nexus

**Join the sovereign AI revolution.**

## Development Workflow

### 1. Fork & Clone
```bash
# Fork on GitHub
# Then clone your fork
git clone https://github.com/YOUR-USERNAME/Mohawk-Nexus.git
cd Mohawk-Nexus

# Add upstream
git remote add upstream https://github.com/rwilliamspbg-ops/Mohawk-Nexus.git
```

### 2. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
# Or for fixes:
git checkout -b fix/your-bug-fix
```

### 3. Develop & Test
```bash
# Write code
# Run tests
./scripts/test.sh

# For specific modules
cd modules/core/sovereign-mohawk-proto
go test ./... -v
```

### 4. Commit with Audit Trail
```bash
git commit -m "Brief description" \
           -m "" \
           -m "Detailed explanation of changes:" \
           -m "- What problem this solves" \
           -m "- How it works" \
           -m "- Any breaking changes" \
           -m "" \
           -m "Assisted-By: Mohawk-Nexus"
```

### 5. Push & Open PR
```bash
git push origin feature/your-feature-name
# Open PR on GitHub with detailed description
```

### 6. Code Review
- Address feedback
- Re-push (don't force unless asked)
- Iterate until approved

### 7. Merge
Maintainers merge once approved.

## Code Standards

### Go
```bash
# Format
gofmt -s -w .

# Lint
golangci-lint run ./...

# Tests
go test -cover ./...
go test -v ./...  # verbose
```

### Python
```bash
# Format
black .

# Lint
pylint --rating-scale=10 .
mypy .  # type checking

# Tests
pytest tests/ -v --cov=.
```

### TypeScript/JavaScript
```bash
# Format
prettier --write .

# Lint
eslint . --fix

# Tests
npm test
npm run test:coverage
```

### Lean4
```bash
# Format
lean --version

# Verify proofs
lean verify --all

# Tests
lake test
```

## Testing Requirements

| Module Type | Coverage | Requirement |
|------------|----------|-------------|
| Core runtime | >90% | Go tests mandatory |
| FL stack | >80% | pytest mandatory |
| Verticals | >70% | npm test + integration |
| Infrastructure | >60% | Basic test suite |

## Security Review Checklist

For ALL pull requests:

- [ ] No hardcoded secrets
- [ ] No eval() / unsafe code
- [ ] Input validation on all external inputs
- [ ] No timing attacks (if crypto)
- [ ] No unencrypted sensitive data
- [ ] Dependency versions verified

## Formal Verification (Core Only)

For consensus changes:

```lean4
-- Prove Byzantine consensus correctness
theorem bft_correct (fault_nodes : ℕ) (total : ℕ) :
  fault_nodes ≤ (total / 3) → eventually_agree_all_honest := by
  sorry  -- Implement proof
```

## Performance Benchmarks

For optimization PRs, include:

```markdown
## Benchmark Results

| Operation | Before | After | Change |
|-----------|--------|-------|--------|
| zk-SNARK verify | 12ms | 9.5ms | -21% |
| BFT round | 250ms | 240ms | -4% |
| Memory/1M nodes | 2.1GB | 1.9GB | -10% |

Tested on: AWS c6i.4xlarge (16 vCPU, 32GB RAM)
```

## Compliance Documentation

For healthcare/climate/etc PRs:

```markdown
## Compliance Checklist

### HIPAA (Healthcare)
- [ ] Patient data not accessed
- [ ] Audit logging enabled
- [ ] Encryption >128bit
- [ ] Access controls enforced

### GDPR (Data Protection)
- [ ] Pseudonymization
- [ ] Encryption keys >256bit
- [ ] Integrity checks
- [ ] Testing documented
```

## Common Tasks

### "How do I run tests locally?"
```bash
./scripts/test.sh           # All tests
go test ./...               # Go only
pytest tests/               # Python only
npm test                    # Node only
```

### "How do I debug a failing test?"
```bash
# Go
go test -run TestName -v

# Python
pytest tests/test_file.py::TestClass::test_method -vv

# Node
npm test -- --verbose
```

### "How do I lint my code?"
```bash
# All
./scripts/format.sh

# Or individually
gofmt -w .
black .
prettier --write .
```

### "How do I add a new module?"
```bash
# Create structure
mkdir -p modules/infrastructure/my-module
cd modules/infrastructure/my-module

# Add appropriate files
touch go.mod         # If Go
touch requirements.txt  # If Python
touch package.json   # If Node
```

### "How do I run only module tests?"
```bash
cd modules/verticals/oncology
npm test

cd modules/orchestration/python-sdk
pytest tests/

cd modules/core/sovereign-mohawk-proto
go test ./...
```

## Release Process

### Version Format
```
v{major}.{minor}.{patch}{-tag}
v1.0.0              # Stable
v1.0.0-alpha        # Alpha
v1.0.0-rc.1         # Release candidate
v1.0.0-post-quantum # Feature release
```

### Release Steps
1. Bump version in all modules
2. Update CHANGELOG.md
3. Tag: `git tag -a v1.0.0 -m "Release 1.0.0"`
4. Push: `git push upstream v1.0.0`
5. Create GitHub Release with notes

### Changelog Format
```markdown
## [1.0.0] - 2026-05-15

### Added
- New zk-SNARK verification (<10ms)

### Changed
- Upgraded to Go 1.21

### Fixed
- Byzantine consensus edge case

### Security
- [SECURITY] Fixed attestation bypass
```

## Module Ownership

| Module | Owner | Backup |
|--------|-------|--------|
| sovereign-mohawk-proto | @core-team | @rwilliamspbg |
| sovereign-map-v2 | @orchestration | @rwilliamspbg |
| oncology | @healthcare | @core-team |
| agriculture | @agritech | @core-team |
| climate | @climate-team | @core-team |
| supply-chain | @logistics | @core-team |

See `.github/CODEOWNERS` for enforcement.

## Support

- **Questions?** GitHub Discussions
- **Bug report?** GitHub Issues (tag module)
- **Security issue?** security@mohawk-nexus.org
- **Docs?** See [`docs/README.md`](README.md)

---

[← Back to Docs Index](README.md)
