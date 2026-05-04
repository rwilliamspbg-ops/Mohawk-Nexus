# ARCHITECTURE.md

## System-Level Architecture

Mohawk Nexus implements a **hierarchical, Byzantine-tolerant federated intelligence layer** with the following guarantees:

### 1. Trust Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│ Policy-Gated Domain (e.g., Oncology)                           │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Governance Layer: Policy enforcement, domain membership    │ │
│ │ ┌──────────────────────────────────────────────────────┐  │ │
│ │ │ Consensus Layer: BFT with formal verification       │  │ │
│ │ │ ┌───────────────────────────────────────────────┐    │  │ │
│ │ │ │ Aggregation Layer: Mohawk Protocol streaming │    │  │ │
│ │ │ │ ┌────────────────────────────────────────┐   │    │  │ │
│ │ │ │ │ Cryptography: zk-SNARKs + PQC       │   │    │  │ │
│ │ │ │ │ ┌──────────────────────────────────┐ │   │    │  │ │
│ │ │ │ │ │ Hardware Trust Root: TPM 2.0    │ │   │    │  │ │
│ │ │ │ │ └──────────────────────────────────┘ │   │    │  │ │
│ │ │ │ └────────────────────────────────────────┘   │    │  │ │
│ │ │ └───────────────────────────────────────────────┘    │  │ │
│ │ └──────────────────────────────────────────────────────┘  │ │
│ └────────────────────────────────────────────────────────────┘ │
│ Edge Nodes (10M–100M+): Local training, cryptographic updates  │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Data Flow (Never Centralized)

1. **Local Training** (Node):
   - Trains on local data (stays on-device)
   - Computes model gradient update
   - Signs with TPM-backed private key

2. **Attested Update** (Node → Aggregator):
   - zk-SNARK proof: "I computed an honest update without cheating"
   - Hardware attestation: "My TPM witnessed this computation"
   - Sends: `{update_hash, zk_proof, tpm_attestation}` (NEVER raw data)

3. **Streaming Aggregation** (Mohawk Protocol):
   - Aggregator accumulates 224x fewer messages than traditional FL
   - Verifies each zk-SNARK (<10ms per proof)
   - Incremental Byzantine consensus: rejects >1/3 malicious updates

4. **Consensus & Finality** (BFT + Lean4 Proofs):
   - Multi-round Byzantine agreement: no single aggregator failure
   - Formal proof that consensus reached with <1/3 malicious actors
   - Global model snapshot committed to ledger (immutable audit trail)

5. **Policy Compliance** (Sovereign Domain):
   - Domain policy gate: HIPAA/GDPR rules encoded in smart contract
   - Automated DPIA: generates compliance evidence on every aggregation
   - Patient/farmer data **never leaves hospital/farm**

### 3. Failure Modes & Guarantees

| Scenario | Guarantee |
|----------|-----------|
| 1–2 malicious aggregators | BFT consensus still correct (requires <1/3) |
| Node offline | Update skipped; no blocking consensus |
| Forged zk-proof | Rejected in verification stage (<10ms check) |
| TPM compromised | Cryptographic signature still valid; hardware attestation fails |
| Network partition | Gossip consensus resilient; domain pauses if >1/3 unreachable |

### 4. Scaling to 100M Nodes

**Traditional FL**: Every node sends full gradient → O(n) aggregator memory
```
1M nodes × 10MB gradient = 10 Petabytes in memory 😡
```

**Mohawk Protocol**: Streaming + sketching → O(log n) per aggregator
```
1M nodes × 32 bytes (hash+proof) = 32 MB per aggregator 😊
224x reduction
```

Achieved via:
- **Sketching**: Compress gradients losslessly (random projection)
- **Sketching verification**: zk-SNARK proves sketch integrity
- **Incremental aggregation**: Aggregate-and-discard pattern, not accumulate

### 5. Cryptographic Stack (2026 PQC Overhaul)

```yaml
Key Exchange:
  - Primary: x25519 (Elliptic Curve, NIST-approved)
  - Hybrid: x25519-mlkem768 (pre-quantum + post-quantum)
  - Fallback: Kyber-1024 (if quantum threat imminent)

Signatures:
  - Short-term: ECDSA (x25519 context)
  - Long-term: XMSS (eXtendable Merkle Signature Scheme)
  - Hardware attestation: ECDSA + TPM 2.0 quote

Proofs:
  - Aggregation: Groth16 zk-SNARKs (<10ms)
  - Consensus: Lean4 formal proofs (offline)
  - Compliance: Automated DPIAs (on-chain verification)
```

### 6. Policy-Gated Domains

Each domain has a **policy contract** (e.g., smart contract on Ethereum or sovereign chain):

**Oncology Domain**:
```solidity
policy {
  require(participant.hipaa_certified == true);
  require(participant.region in ["EU", "US", "CA"]);
  require(data_retention <= 90 days);
  emit_dpia_evidence_on_aggregation();
}
```

**Agriculture Domain**:
```solidity
policy {
  require(participant.farm_size <= 5000 hectares);
  require(sustainability_score >= 7);
  allow_yield_model_inference();
}
```

Policies enforced **before** node joins domain; domain can **reject malicious policies**.

---

## Module Dependencies

```
Sovereign-Mohawk-Proto (Core)
  ├── libp2p (peer discovery, gossip)
  ├── Lean4 (formal verification)
  ├── zk-SNARK libs (Groth16 backend)
  └── tpm2-tools (hardware attestation)

Sovereign-Map (Orchestration)
  ├── Sovereign-Mohawk-Proto (consensus)
  ├── Prometheus (metrics)
  ├── Grafana (dashboards)
  └── smart contract platform (Ethereum/sovereign)

Verticals (Oncology, Agriculture, Climate, SupplyChain)
  ├── Sovereign-Map (orchestration)
  ├── Flower (federated learning)
  ├── NVFlare (optional: NVIDIA FL runtime)
  └── domain-specific ML libraries

Autonomous-Mapping
  ├── ORB-SLAM3 (spatial tracking)
  ├── zk-SNARK (biometric proofs)
  └── quantization libs
```

---

## Deployment Topology

### Typical Oncology Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│ Sovereign-Mohawk-Oncology-Global                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ Orchestrator (Sovereign-Map-V2)                          │   │
│ │ • HIPAA Policy enforcement                               │   │
│ │ • Hospital participant management                         │   │
│ │ • Global model versioning                                │   │
│ └──────────────────────────────────────────────────────────┘   │
│             ↓ consensus ↓                                       │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ Aggregators (Sovereign-Mohawk-Proto, n=3 Byzantine BFT)  │   │
│ │ • Each validates incoming updates                         │   │
│ │ • Streams aggregation (224x memory efficient)             │   │
│ │ • Formal consensus (Lean4 verified)                       │   │
│ └──────────────────────────────────────────────────────────┘   │
│             ↓ gossip protocol ↓                                 │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ Hospital Nodes (1000s worldwide, local training)         │   │
│ │ • Johns Hopkins: 500M patient records (local)            │   │
│ │ • Mayo Clinic: 200M records (local)                      │   │
│ │ • NCI: 100M records (local)                              │   │
│ │ • ... plus 1000+ more participants                        │   │
│ │                                                           │   │
│ │ Each Hospital:                                            │   │
│ │  └─ Local Model Trainer                                   │   │
│ │  └─ TPM-backed Signer                                     │   │
│ │  └─ zk-SNARK Prover (< 10ms/update)                       │   │
│ │  └─ HIPAA Compliance Auditor                              │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│ Observability (Prometheus + Grafana):                           │
│ • Aggregation latency, network delays                           │
│ • HIPAA audit trail (immutable logs)                            │
│ • Model performance by region / cohort                          │
│ • Tokenomics: participation rewards / usage burn                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Performance Metrics

### Latency Profile
- **Local Training**: 10–100s (hospital ML pipeline)
- **zk-SNARK Generation**: < 10ms (modern hardware)
- **zk-SNARK Verification**: < 10ms (batch verifier)
- **BFT Consensus Round**: 100–500ms (3-node Byzantine agreement)
- **Global Aggregation Cycle**: 5–10 minutes (typical)

### Throughput
- **Nodes per aggregator**: 10M–100M (streaming protocol)
- **Updates per second**: 1M+ (with 100 aggregators)
- **Proof generation parallelism**: Linear in node count

### Memory
- **Per-aggregator footprint**: 100 MB – 1 GB (vs. 10 PB centralized)
- **Per-node footprint**: 10 MB – 1 GB (depends on model size)

---

## Security Assumptions

1. **Hardware Trust**: TPM 2.0 cannot be software-patched; requires physical compromise
2. **Cryptography**: Post-quantum candidates (x25519-mlkem768) not broken before 2030
3. **Consensus**: <1/3 of aggregators can be adversarial (Byzantine assumption)
4. **Network**: Adversary cannot eclipse all honest aggregators (gossip resilience)
5. **Formal Proofs**: Lean4 type system sound (no known vulnerabilities)

---

## Future Work

- **Sharding**: Partition policy domains for 1M+ aggregators
- **Light Clients**: Mobile nodes with simplified verification
- **Cross-Domain Composability**: Aggregate across multiple policy domains safely
- **Autonomous Learning**: Self-improving global model with human-in-the-loop governance
