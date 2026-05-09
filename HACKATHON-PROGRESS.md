# Hackathon Progress Tracker

## Current Plan

- Primary demo: Agentic Sovereignty Console
- Runtime layer: AG-UI
- Render layer: A2UI
- Proof layer: Prometheus scrape on port 9090
- Optional bonus: MCP Apps only if the core flow is stable

## Done

- [x] Created the concrete hackathon plan in [HACKATHON-GENUI-PLAN.md](HACKATHON-GENUI-PLAN.md)
- [x] Updated [README-HACKATHON.md](README-HACKATHON.md) to point to the current plan
- [x] Reframed [site/index.html](site/index.html) around the Agentic Sovereignty Console
- [x] Added a small interactive console that simulates the AG-UI to A2UI flow
- [x] Extended the console to show Prometheus-scraped verification on port 9090
- [x] Updated the plan to include a Prometheus proof surface in the end-to-end flow
- [x] Expanded the frontend into a fuller agentic console with mission controls, telemetry, and an event log

## In Progress

- [ ] Convert the simulated console into a real AG-UI or agent-driven data flow
- [ ] Update any remaining hackathon docs that still frame the old 3-demo strategy as primary
- [ ] Decide whether to connect the proof surface to a real metrics exporter or leave it as a demo-time scrape story

## Not Done

- [ ] Build a real backend/runtime integration for the console
- [ ] Add a true A2UI renderer path instead of the local state machine
- [ ] Add an MCP Apps flourish only after the core flow is reliable
- [ ] Validate the Pages deployment after any future documentation or demo changes
- [ ] If needed, wire an actual Prometheus exporter before relying on live scrape checks

## Next Steps

1. Decide whether the next implementation pass should focus on a real runtime hookup or a real metrics exporter.
2. If runtime comes first, replace the local demo state machine with a server-backed endpoint or agent bridge.
3. If docs come first, finish converting any remaining hackathon docs to the new single-path strategy.
4. Keep this file updated after each completed slice so the current state stays obvious.

## Update Rule

Whenever work changes, update three things here:

1. What is done.
2. What is not done.
3. What the next step is.
