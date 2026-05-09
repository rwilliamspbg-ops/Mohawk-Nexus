# Mohawk Nexus Demo Brief

Mohawk Nexus is presented here as a judge-facing systems demo: one image, one story, and one stack that shows sovereign aggregation, proof, and efficiency at scale.

## The Tech in One Image

```text
Edge Nodes (100K-1M)
		↓ (local training)
Byzantine Consensus Layer
		↓ (BFT agreement)
Mohawk Aggregation Protocol  ← O(d log n) memory scaling
		↓ (lossless sketching)
zk-SNARK Verification  ← <10ms proof of correctness
		↓
OUTPUT: Verified intelligence, no central authority
```

## Key Stats

Tell judges these numbers:

| Stat | Why |
|---|---|
| O(d log n) | Algorithmic superiority versus O(n) bloat |
| 224x RAM reduction | Concrete efficiency proof |
| 1/3 Byzantine threshold | Tolerates malicious nodes |
| <10ms SNARK proof | Real-time verification |
| 100M nodes | Planetary scale |
| 31x memory savings | Per aggregator, 100k nodes |
| Electricity + water savings | Sustainability angle |
| 58MB edge runtime | Works on constrained hardware |

## Demo Flow

### Demo 1: Agentic Sovereignty

Opening line:

> Watch 100 sovereign nodes aggregate intelligence in real-time.

Suggested visual path:

1. Open the animated node network.
2. Point at the timeline where each aggregation triggers a zk-SNARK proof.
3. Show the proof marker appearing consistently.
4. Inject one fault and show the proof fail.
5. Close with the message: trustworthy intelligence at scale.

Time: about 2 minutes.

### Demo 2: Efficiency

Opening line:

> Same aggregation. Look at the resource drain.

Suggested visual path:

1. Show the side-by-side comparison.
2. Point to the centralized path with high RAM, electricity, and water usage.
3. Point to the SMP path with low RAM and lower environmental cost.
4. End on the sustainability message.

Time: about 2 minutes.

## If Stuff Breaks

Use these fallback lines if the live demo stalls:

1. **Demo crashes?**
	 > Let me show you the code. This is where the magic is.

2. **Forgot a stat?**
	 > The key insight is that we reduced aggregation from linear to logarithmic complexity.

3. **No internet?**
	 > Let me run it locally.

4. **Ran out of time?**
	 > Here’s the repo. Everything is open-source, and we’d love your feedback.

## Close Strong

Pick the closing line based on the audience:

- **Technical judges:**
	> This is formally verified Byzantine consensus with post-quantum cryptography. Lean4 proofs. Production-ready.

- **Sustainability judges:**
	> AI’s hidden environmental cost is infrastructure. We’re making that infrastructure sustainable.

- **Business judges:**
	> Every enterprise federation needs this. Healthcare, agriculture, supply chains. We’re the infrastructure layer.

- **Hacker judges:**
	> Edge AI just became viable. 58 megabytes with full Byzantine tolerance. The future of agentic systems lives at the edge.

## Questions To Hope For

Q: “So this is just federated learning?”

> No. FL trains models locally. We aggregate outputs from trained models, which is a different problem and a different solution.

Q: “How do you prevent bad nodes?”

> Byzantine consensus. If 1/3 or fewer are malicious, math guarantees convergence to the honest aggregate.

Q: “Will this really get deployed?”

> Absolutely. Healthcare, agriculture, and supply chains all need infrastructure they do not have to centrally trust.

Q: “What’s the O(d log n) thing?”

> d is model dimension and n is node count. Traditional aggregation needs O(n) memory; this stays logarithmic.

## What Judges Should Remember

You are not showing:

- Another ChatGPT wrapper
- Prettier UI
- Faster inference
- More model parameters

You are showing:

- Trustworthy infrastructure
- Formal mathematical proofs
- Planetary-scale systems thinking
- Sustainability
- Edge computing

## Demo Surfaces In This Repo

- [site/index.html](site/index.html) - unified dashboard and main entry point.
- [site/minimal-ui.html](site/minimal-ui.html) - Proto-focused operational UI with live metrics, attestation, and audit logging.
- [site/prometheus-headless.html](site/prometheus-headless.html) - headless Prometheus dashboard.

## Local Run

Serve the repository root and open the pages in a browser.

```bash
python3 -m http.server 8000
```

Then open:

- `http://localhost:8000/site/index.html`
- `http://localhost:8000/site/minimal-ui.html`
- `http://localhost:8000/site/prometheus-headless.html`

## Deeper Docs

Use the other markdown files in the repository for architecture, deployment, troubleshooting, security, and roadmap details.
