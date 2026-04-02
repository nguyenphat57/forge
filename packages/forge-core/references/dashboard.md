# Forge Dashboard Reference

Use this reference when:

- the dashboard read model needs to expose more packet or release state
- you need to decide whether a field belongs in workflow-state or only in the dashboard view
- an operator asks for a quick scan surface for active packets, browser QA pending, or next merge point

Rules:

- the dashboard is a thin view over persisted artifacts
- do not invent progress percentages, throughput scores, or vanity telemetry
- add dashboard fields only when they materially improve resume, review, merge, or release decisions
- if a field matters enough to drive behavior, prefer putting it in workflow-state first and reading it from the dashboard second
