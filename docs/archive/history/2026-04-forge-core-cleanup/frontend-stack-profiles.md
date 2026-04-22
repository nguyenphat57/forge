# Frontend Stack Profiles

Archived from `packages/forge-core/references/frontend-stack-profiles.md` on 2026-04-22 during forge-core cleanup tranche 4.
This file describes a retired optional frontend-lens helper and remains for historical context only.

## generic-web

- Suitable when the stack is unclear or the task is still in UI reasoning before implementation.
- Prioritize semantics, tokens, interaction cues, and responsive states.
- Do not default to framework-specific patterns when the artifact is not yet proven.

## html-tailwind

- Prioritize utility clarity, extracted patterns, theme tokens, stable hover/focus states.
- Watchouts:
  - class soup
  - too many arbitrary values
  - `transition-all`
  - surfaces that disappear in light mode

## react-vite

- Prioritize component boundaries according to screen regions and state ownership.
- Clearly define loading, empty, and error paths in the brief before coding.
- Watchouts:
  - Layout depends on unnecessary temporary state
  - polished animation hides rerender or state complexity

## nextjs

- Separate the server/client boundary before describing complex interactions.
- Include loading and streaming placeholders in the UX contract.
- Watchouts:
  - design depends on client-only state without fallback
  - hydration edge cases distort the visual plan

## mobile-webview

- Use for Capacitor, webview, or tablet POS-style work.
- Prioritize touch targets, safe-area handling, keyboard behavior, and viewport resize resilience.
- Watchouts:
  - hover-centric interactions
  - actions placed close to the gesture area
  - dense layouts that only look good on desktop

## Reading Rule

- Only select the profile closest to the stack or task.
- If the stack is still unclear, use `generic-web`.
- If visual exploration is for a mobile or tablet shell, `mobile-webview` is usually more useful than `generic-web`.
