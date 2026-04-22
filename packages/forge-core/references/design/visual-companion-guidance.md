# Visual Companion Guidance

Use the visual lens inside `forge-brainstorming`, not a separate design stage. The protocol should mirror Superpowers `brainstorming` as closely as Forge allows. The legacy `/visualize` alias may still route here, but the canonical process remains `forge-brainstorming`.

## Offer Protocol

Before clarifying questions, offer the companion when upcoming questions may involve mockups, diagrams, visual comparisons, layout, hierarchy, or architecture shape.

This offer MUST be its own message. Do not combine it with clarifying questions, context summaries, tradeoff lists, or any other content.

Offer shape:

```text
Some of what we're working on might be easier to explain if I can show it in a browser. I can put together mockups, diagrams, comparisons, and other visuals as we go. Want to try it? This requires opening a local URL.
```

If declined, continue text-only. If accepted, decide per question whether the browser helps.

## Tool Protocol

Start the bundled Forge server from the workspace root:

```bash
tools/visual-companion/scripts/start-server.sh --project-dir <workspace>
```

On Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File tools/visual-companion/scripts/start-server.ps1 -ProjectDir <workspace>
```

The session persists under:

```text
<workspace>/.forge-artifacts/visual-companion/<session-id>
```

Treat the `server-started` JSON as the contract:
- `url` is the local browser URL to open
- `screen_dir` receives HTML fragments or full HTML documents
- `state_dir/events` records click choices from `[data-choice]` elements
- adding a new HTML file clears old choice events and reloads the browser through WebSocket
- returning to terminal-only work should show a waiting screen or stop the server with `stop-server.*`

HTML fragments are wrapped in the Forge frame automatically. Full HTML documents are served as-is with the helper script injected before `</body>`.

## Per-Question Decision

Use the browser when:
- layout, hierarchy, responsiveness, or interaction shape can change the design decision
- a screen, dashboard, form, onboarding flow, or dense data view needs a concrete visual companion
- mobile, tablet, accessibility, or motion behavior is part of the success signal
- the user asks for a mockup, sketch, visual direction, or visual comparison
- architecture diagrams, flowcharts, state machines, or relationships are easier to judge visually

Use the terminal when:
- the answer is requirements, scope, or success criteria
- options are conceptual and can be compared as text
- the decision is technical rather than visual
- the question is clarifying rather than asking for visual preference

A visual topic is not automatically a visual question.

## Route Boundary

Keep the Forge route flat:

```text
brainstorm -> plan -> build
```

The design doc should record:
- why the visual lens was useful
- what visual decision it informed
- which visual constraints the implementation plan must preserve

Do not use the visual lens to skip design approval or plan execution choice.
