# Proto + Venmo Demo

Mohawk Nexus is now presented as a single narrated demo that combines a protocol console with a Venmo-style payment flow.
The goal is to show a clean, judge-friendly product story: one side proves protocol state, the other side shows a familiar consumer payment action, and both are tied together by live telemetry.

## What this demo shows

The demo is built around two connected experiences:

1. **Proto** - a protocol control surface that runs step-based sequences, shows live trace output, and records secure command attestations.
2. **Venmo-style transfer flow** - a fast payment narrative that demonstrates sending, confirming, and tracking a transfer in a way that feels instantly recognizable.

The important idea is not just that the UI looks polished. It is that the demo makes a technical workflow feel understandable in seconds.

## Why this matters

Most demos show separate panels with no story.
This one is designed to feel like a product walkthrough:

- Proto explains what the system is doing.
- The payment flow shows why the action matters to a user.
- Prometheus keeps the telemetry visible.
- The pages stay usable even if the data source is slow or unavailable.

## Demo pages

The repo includes three main surfaces:

- [site/index.html](site/index.html) - the main unified dashboard with fleet, protocol, commands, map, and metrics views.
- [site/minimal-ui.html](site/minimal-ui.html) - the full Proto-focused action UI with live metrics, attestation, and audit logging.
- [site/prometheus-headless.html](site/prometheus-headless.html) - the headless telemetry dashboard for Prometheus-only monitoring.

## Recommended demo flow

Use this sequence when presenting the repo:

1. Open the main dashboard in [site/index.html](site/index.html).
2. Switch to the Proto tab and run a short sequence.
3. Show the command attestation and audit trail.
4. Open the Prometheus view and point out the live telemetry.
5. Use the payment-style story to explain how the demo maps protocol output to a real user action.

## What to say in the room

A short version of the story is:

> This demo combines a protocol console and a Venmo-style transfer experience so the user can see both the system state and the user-visible effect. Proto explains the logic, Prometheus proves the telemetry, and the interface stays simple enough to understand immediately.

## Local usage

If you want to inspect the pages locally, serve the repository root and open the `site/` pages in a browser.

Example:

```bash
python3 -m http.server 8000
```

Then open:

- `http://localhost:8000/site/index.html`
- `http://localhost:8000/site/minimal-ui.html`
- `http://localhost:8000/site/prometheus-headless.html`

## Repository notes

- The unified dashboard in [site/index.html](site/index.html) is the main entry point.
- The Proto UI in [site/minimal-ui.html](site/minimal-ui.html) is the best place to review the step runner, trace log, and command attestation.
- The headless telemetry page in [site/prometheus-headless.html](site/prometheus-headless.html) is the cleanest Prometheus-only surface.
- The hackathon docs under the root still explain the broader protocol and demo plan.

## Positioning

This repository is now easiest to understand as a product demo rather than a raw documentation bundle.

The core message is:

- Proto gives the system a readable, inspectable workflow.
- The Venmo-style flow makes that workflow feel like a real user action.
- Prometheus gives you a proof surface outside the UI.
- The whole demo stays lightweight enough to present without a long setup.

## If you need the deeper docs

Use the other markdown files in the repository for architecture, deployment, troubleshooting, security, and roadmap details.
Those documents remain the technical reference layer underneath this demo README.
