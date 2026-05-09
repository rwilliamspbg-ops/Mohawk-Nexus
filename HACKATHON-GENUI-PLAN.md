# Mohawk Nexus Hackathon Plan: Agentic Sovereignty Console

## Goal

Build one polished, judge-ready demo that makes Mohawk Nexus feel like a real agentic interface product rather than a research prototype.

### Primary protocol choice

Use AG-UI as the interaction layer and A2UI as the live presentation layer.

Why this is the best fit:

1. It matches the current repository story: sovereignty, verification, and agentic interfaces.
2. It is the lowest-risk way to make the demo feel hands-on and interactive.
3. It reuses the existing site, pitch, and hackathon timeline without forcing a rebuild.
4. It gives judges a concrete artifact they can watch change in real time.

### Secondary protocol choice

Add MCP Apps only as a small bonus surface if the core demo is stable.

Use it for one open-ended artifact, such as an editable architecture sketch or a proof explanation panel. Do not make MCP Apps the main path.

## Demo Concept

The demo is called the Agentic Sovereignty Console.

It shows three live zones:

1. A control panel where the agent receives a request and chooses the next action.
2. A declarative A2UI surface that renders live state, proof status, and node metrics.
3. A short evidence trail that shows the protocol verified the response rather than just generating text.

## What judges should understand

The message is simple:

1. The agent is not just chatting.
2. The interface is being shaped by the agent at runtime.
3. The data is verifiable and not centrally trusted.
4. The system still feels polished and usable.

## What to build

### Core deliverables

1. A landing view inside [site/index.html](site/index.html) that frames the demo and explains the protocol choice.
2. One A2UI-rendered live panel for protocol state.
3. One AG-UI interaction loop that drives the panel updates.
4. One proof or verification badge that changes state as the interaction proceeds.
5. One Prometheus-scraped proof surface on port 9090 that mirrors the same verification state outside the UI.
6. A fallback static version of the same demo that still tells the story if the agent layer fails.

### Optional bonus deliverable

1. A small MCP Apps surface for an editable diagram, not the core workflow.

## Build order

### Phase 1: Lock the story

1. Update the pitch to say the demo is an agentic console with A2UI rendering and AG-UI control.
2. Keep the sustainability and sovereignty framing from [PITCH.md](PITCH.md).
3. Avoid adding new narrative branches.

### Phase 2: Make the UI explicit

1. Replace static panels with one live A2UI-driven surface.
2. Show at least one state transition: idle -> analyzing -> verified.
3. Keep the visual language aligned with the existing dark, high-contrast site.

### Phase 3: Wire the interaction loop

1. Use AG-UI for the runtime handoff.
2. Feed the agent a small fixed task, such as evaluating node health or verifying an aggregate.
3. Render the result in the A2UI surface.

### Phase 4: Add proof value

1. Show a proof badge, verification timestamp, or deterministic result hash.
2. Make the verification visible, not implied.
3. Tie the proof status to the current panel state.
4. Mirror the same signal through Prometheus on port 9090 so the judge can inspect the run outside the page.

### Phase 5: Add the flourish only if stable

1. Add one MCP Apps artifact if the main path is already reliable.
2. Keep it visually simple and obviously secondary.
3. Stop before the demo becomes fragile.

## 6-hour execution plan

### Hour 0-1: Setup and commit the narrative

1. Open the existing site and make sure it is the demo shell.
2. Write the protocol choice into the homepage or demo header.
3. Decide the single user journey: request -> agent action -> rendered UI -> verification.

### Hour 1-2: Build the A2UI surface

1. Implement one panel for live state.
2. Keep the data model tiny.
3. Use the simplest possible update path that still looks dynamic.

### Hour 2-3: Connect AG-UI interactions

1. Drive the panel through a single action flow.
2. Make sure the state changes are visible.
3. Verify the UI still loads cleanly on refresh.

### Hour 3-4: Add proof and metrics

1. Add the verification badge.
2. Add one or two metrics that support the story.
3. Remove anything that does not help the judge understand the point in under 10 seconds.

### Hour 4-5: Polish and stabilize

1. Fix layout, spacing, and labels.
2. Make the transitions obvious.
3. Test the fallback static state.

### Hour 5-6: Demo rehearsal

1. Practice the pitch and the click path.
2. Prepare one fallback screenshot or static page view.
3. Keep the final demo short enough to survive under pressure.

## Success criteria

The plan is successful if all of the following are true:

1. A judge can see the agent driving the interface.
2. A2UI is visibly doing real work in the UI.
3. Prometheus on port 9090 exposes the same proof signal outside the UI.
4. The demo feels credible even if the optional MCP piece is removed.
5. The story remains aligned with Mohawk Nexus: sovereignty, verification, and efficiency.

## What not to do

1. Do not make MCP Apps the primary demo path.
2. Do not spread effort across all three protocol styles equally.
3. Do not sacrifice reliability for extra features.
4. Do not replace the current narrative with a generic chatbot demo.

## Final recommendation

Build AG-UI + A2UI first, treat MCP Apps as optional, mirror proof through Prometheus on port 9090, and present the result as an Agentic Sovereignty Console.
