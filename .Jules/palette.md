## 2026-07-11 - [Reduced Motion and Focus Isolation on Dynamic Network Visualizations]
**Learning:** Highly animated WebGL or Canvas-like background decorations (e.g., neural network node/edge grids) pose vestibular and cognitive accessibility hazards. Disabling CSS animations alone via `prefers-reduced-motion` can leave active requestAnimationFrame loops spinning in JavaScript, causing background battery drain and rendering jank.
**Action:** Detect `window.matchMedia('(prefers-reduced-motion: reduce)').matches` directly in JavaScript to conditionally abort loop registrations and hide background visualizers entirely, while concurrently overriding transition and animation properties in global CSS.

## 2026-07-12 - [Contrast Violations on Secondary Gradients and Screen Reader Optimization]
**Learning:** Cyberpunk or dark-mode pages often use neon/vibrant accents which can conflict with standard text colors. The secondary action buttons here placed dark/black text against a deep purple-blue gradient, violating WCAG AA/AAA contrast guidelines. Additionally, decorative emojis in headings/badges lead to vocalized clutter in assistive technologies without proper masking.
**Action:** Explicitly define high-contrast white text (`#ffffff`) for any interactive element layered on top of medium/dark gradients, hide decorative emojis using `aria-hidden="true"`, and implement semantic landmarks with a keyboard-focusable "Skip to Content" link.

## 2026-07-13 - [Visual Parity for Multi-window Links and Keyboard-accessible Back-to-Top Tooltips]
**Learning:** Visual parity between assistive technology (screen reader `sr-only` text) and visual presentation is essential. Landing pages with multiple repositories/external links opening in new tabs should provide unified visual feedback to avoid unexpected context switches. Additionally, hover-and-focus tooltips can be constructed with pure, accessible CSS on existing buttons without any runtime DOM or JS overhead.
**Action:** Always combine `sr-only` descriptive screen-reader instructions with an inline, visually responsive SVG icon that transforms subtly on hover to denote external navigation, and deploy CSS-only absolute-positioned tooltips with focus-visible compatibility for keyboard-navigated discoverability.

## 2026-07-14 - [Balancing Interaction Complexity Against Scope Budgets on Micro-UX Tasks]
**Learning:** For landing pages with highly interactive but localized widgets (like clipboard-copying), trying to implement multi-step or multi-shortcut help models can quickly exceed strict micro-UX budget bounds (e.g., < 50 lines) and introduce fragile focus-trapping routines. A sleek Toast alert provides excellent feedback with a fraction of the line count and fits seamlessly into standard accessibility patterns.
**Action:** Prioritize lightweight, self-clearing toast notifications using native `aria-live` regions over heavy modal dialogs when the user goal is simple confirmation or action feedback.
