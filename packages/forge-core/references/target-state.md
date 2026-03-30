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
