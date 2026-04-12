# Forge Target State

Date: 2026-03-29
Status: target-state manifesto
Inputs:
- `docs/PRODUCT_THESIS_2026-03-29.md`
- `docs/archive/plans/2026-03-29-forge-tdd-sdd-adoption-roadmap.md`
- `packages/forge-core/references/artifact-driven-change-flow.md`

## Manifesto

Forge should become the most dependable process-first execution system for a solo developer shipping real work in a real repo.

The end state is not "more workflow" or "more AI."
The end state is trust:
- trust that Forge understands the work before it edits
- trust that Forge keeps important state outside the chat
- trust that Forge does not claim progress without proof
- trust that Forge still helps when the repo is messy, old, or unfamiliar

Forge should feel lightweight on small tasks, structured on medium tasks, and strict on high-risk work.
It should adapt its ceremony to the risk, not force the same ritual everywhere.

## Product Promise

When a solo developer uses Forge, they should get three things reliably:
- a clearer next move than they had before
- a safer path from intent to verified change
- durable evidence that survives beyond the current session

Forge is successful when it reduces guesswork, hidden state, and false confidence.
Forge fails when it produces fluent activity without inspectable proof.

## What Forge Must Be

Forge must be:
- spec-aware before build
- artifact-driven during execution
- evidence-backed at handoff
- brownfield-first in repo behavior
- stack-agnostic at the core
- useful even without any companion

Forge should make good process visible:
- what is being changed
- why it is being changed
- what proof exists
- what risks remain
- what the next gate is

## What Forge Must Not Become

Forge must not become:
- a prompt wrapper with no durable state
- a ceremony machine that slows every small task
- a companion-dependent product whose core is weak without add-ons
- a framework-specific opinion disguised as a general tool
- a system that treats "looks done" as equivalent to "verified"

## Operating Laws

Every meaningful change should move Forge closer to these laws:

1. Understand before acting.
Clarify intent, constraints, and affected behavior before code changes on anything medium or risky.

2. Artifacts over chat memory.
Important decisions, plans, specs, verification, and review state should live in repo-visible artifacts.

3. Verification before claims.
Forge should earn words like `done`, `ready-for-review`, and `ready-for-merge`.

4. Risk scales process.
The higher the ambiguity or blast radius, the stronger the spec, review, and proof requirements.

5. Small tasks stay small.
Forge should not drag trivial work through heavyweight ceremony unless the risk demands it.

6. Brownfield is the default.
Repo onboarding, change safety, and continuity matter more than greenfield novelty.

7. Companions are accelerators, not crutches.
They may deepen stack support, but they must not replace core discipline.

## Decision Filter

Use this document as a filter for future changes.

A change is directionally good if it makes Forge better at one or more of these:
- turning rough intent into a correct next action
- preserving state across sessions and agents
- checking changes against specs, tasks, and proof
- helping users operate safely in existing repos
- making review and merge readiness inspectable

A change is directionally bad if it mainly adds:
- ceremony without better decisions
- output volume without better evidence
- stack bias inside the core
- cleverness that hides process state
- convenience that weakens verification

## Target User Experience

At its best, Forge should feel like this:
- on a small fix, it is fast and direct
- on a medium change, it becomes organized and artifact-driven
- on a risky change, it becomes explicit, skeptical, and reviewable
- after any meaningful session, another person or another agent can resume from the artifacts without guessing

## Bottom Line

Forge should be the system a solo developer trusts when the work is real, the repo is imperfect, and the cost of being confidently wrong is high.

That is the target state.
If a future change does not move Forge toward that state, it should be challenged before it lands.
