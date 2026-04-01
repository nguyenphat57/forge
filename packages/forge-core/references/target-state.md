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

## Deferred Boundary

The following belong to `1.13+` unless a later `1.12.x` slice explicitly promotes them:

- installed-runtime health or doctor-style live host verification: defer because `1.12.x` is about operating-model maturity, not adding new live-host trust surfaces.
- host rollout ledgers: defer because the current release-tail contract already records enough state for solo-dev maturity without introducing a second tracking system.
- runtime canary expansion beyond the release contract already in place: defer because `1.12.x` should strengthen the existing release loop before widening the canary surface.
- generated release publish packets: defer because publish automation is packaging acceleration, not a blocker for the `1.12.x` operating model.
- deeper companion acceleration or broader companion breadth: defer because `1.12.x` must keep core solo-dev behavior coherent before adding more companion-dependent leverage.

If a proposed release tier does not change the behavior bar, keep the canonical tier list smaller and preserve compatibility aliases instead of creating new posture names.
