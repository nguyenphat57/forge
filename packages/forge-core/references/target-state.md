# Forge Target State Reference

> Goal: keep Forge maintenance and operator guidance aligned with the product target state instead of drifting into local optimizations.

Canonical source-repo manifesto:
- `docs/FORGE_TARGET_STATE_2026-03-29.md`

Read this reference when:
- deciding between two valid implementation directions for Forge itself
- adding or removing process, artifacts, or review gates
- considering a new core dependency on a companion, runtime tool, or stack-specific layer
- deciding whether a shortcut improves delivery or only weakens verification

## North Star

Forge should be the most dependable process-first execution system for a solo developer shipping real work in a real repo.

That means Forge should be:
- lightweight on small tasks
- structured on medium tasks
- strict on high-risk work
- artifact-driven during execution
- evidence-backed at handoff
- useful in brownfield repos, not only ideal greenfield setups

## Decision Filter

Prefer a change when it improves one or more of these:
- clearer next action from ambiguous intent
- stronger repo-visible state across sessions and agents
- better proof before `ready-for-review`, `ready-for-merge`, or `done`
- safer execution in existing repos
- clearer review, gate, and residual-risk visibility

Challenge a change when it mainly adds:
- ceremony without better decisions
- output volume without better evidence
- stack bias inside the core
- convenience that weakens verification
- chat fluency that replaces durable artifacts

## Non-Negotiables

- Medium and risky work should prefer artifacts over chat memory.
- Verification language must be earned with fresh proof.
- Companions may accelerate delivery, but they must not become core crutches.
- Brownfield safety matters more than greenfield spectacle.

## 1.12.x Target

`1.12.x` should make Forge feel operationally mature for a solo developer without changing the product thesis:

- workflow-state should become the default backbone for medium+ and release-sensitive work
- release posture should be explicit, but not over-fragmented into tiers that do not change behavior
- adoption-check should remain a bounded post-release signal, not an analytics layer
- help and next should read the actual operating state instead of inventing guidance from repo shape alone
- adapter surfaces should tell one coherent story about routing, gates, and aliases

## 1.13.x Target

`1.13.x` should make build execution feel as intentional as release execution:

- medium and large build work should default to a build packet instead of loose checkpoints
- `track_execution_progress.py` should stay the canonical packet source of truth, while summaries and adapters remain read models
- help and next should resume the active packet, pending proof, and next merge point from workflow-state instead of reconstructing the slice from chat
- host-native acceleration should preserve one packet contract across `controller-sequential`, `independent-reviewer`, and `parallel-split`
- browser QA should stay targeted, packet-scoped, and evidence-backed instead of becoming a generic mandatory gate

## 1.14.x Target

`1.14.x` should increase execution throughput without contract drift:

- fast lane is explicit for small low-risk slices, but it still keeps proof-before-claims, verification rerun, and residual-risk capture
- packet graph fields are canonical in packet state (`depends_on_packets`, `unblocks_packets`, merge intent, overlap risk, readiness, and completion gate)
- runtime health and doctor-style diagnostics are explicit for browser-capable runtime paths before claiming browser proof
- host capability contract v2 stays explanatory (`tier`, dispatch reasons, fallback reasons) without changing packet semantics
- continuity depth stays bounded through a packet index read model that summarizes packet state without replacing workflow-state
- extension and preset boundaries stay narrow: packet templates, workflow overlays, and planning presets cannot override core verification and state contracts
- onboarding stays thin: first-run guidance should help a solo operator start quickly without hiding process expectations

## Deferred Boundary

The following stay deferred beyond `1.14.x` unless a later slice narrows them first:

- host rollout ledgers: defer because the release-tail workflow-state already carries enough control without adding a second tracking system
- runtime canary expansion beyond the release contract already in place: defer until the bounded runtime health contract proves stable in real repos
- generated release publish packets: defer because publish automation is packaging acceleration, not execution-kernel leverage
- cloud-synced memory or self-healing control loops: defer until a local execution-facing use case proves a clear payoff
- breadth-first companion expansion: defer until current bounded extension and preset surfaces are stable and measurable

If a proposed release tier does not change the behavior bar, keep the canonical tier list smaller and preserve compatibility aliases instead of creating new posture names.
