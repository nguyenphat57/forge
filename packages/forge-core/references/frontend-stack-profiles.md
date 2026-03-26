# Frontend Stack Profiles

> Used when the frontend task needs a specific lens according to the stack instead of a general guideline.

## generic-web

- Suitable when the stack is unclear or the task is UI reasoning before implementation.
- Prioritize semantics, tokens, interaction cues, responsive states.
- Do not default to framework-specific patterns when the artifact is not yet proven.

## html-tailwind

- Prioritize utility clarity, extracted patterns, theme tokens, stable hover/focus states.
- Watchouts:
  - class soup
  - Arbitrary values ​​​are rampant
  - `transition-all`
  - Surface is too clear in light mode

## react-vite

- Prioritize component boundaries according to screen regions and state ownership.
- Clearly define loading/empty/error path in the brief before coding.
- Watchouts:
  - Layout depends on unnecessary temporary state
  - polish animation hides rerender or state complexity

## nextjs

- Separate the server/client boundary before describing complex interactions.
- Include loading and streaming placeholders in the UX contract.
- Watchouts:
  - design depends on client-only state without fallback
  - hydration edge cases pull out visual plan

## mobile-webview

- Used for Capacitor/webview/tablet POS style work.
- Prioritize touch targets, safe-area, keyboard behavior, viewport resize resilience.
- Watchouts:
  - hover-centric interactions
  - actions placed close to the gesture area
  - dense layout only looks good on desktop

## Reading Rule

- Only select the profile closest to the stack/task.
- If the stack is still unclear, use `generic-web`.
- If visual exploration is for mobile/tablet shell, usually `mobile-webview` is more useful than `generic-web`.
