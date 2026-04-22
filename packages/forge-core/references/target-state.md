# Forge Target State Reference

> Goal: keep Forge aligned with the split-skill, host-neutral, invariant-guarded contract instead of drifting back toward script-first or host-specific control.

Canonical source-repo manifesto:

- `docs/FORGE_TARGET_STATE_2026-03-29.md`

Current maintainer docs:

- `docs/current/architecture.md`
- `docs/current/operator-surface.md`
- `docs/current/install-and-activation.md`

Read this reference when:

- deciding whether a Forge change preserves the markdown-first public contract
- deciding whether a new helper belongs in sibling skill markdown, workflow-state, or deterministic tooling
- deciding whether a host convenience weakens or preserves host-neutral skill meaning
- deciding whether a shortcut improves operator clarity or just moves control out of durable artifacts

## North Star

Forge should be the most dependable evidence-first execution kernel for a solo developer working in a real repo.

That means Forge should be:

- markdown-first for control
- skill-first for activation
- workflow-first in behavior
- host-neutral in public meaning
- invariant-guarded where state, verification, or preferences need machinery
- lightweight on small work
- structured on medium work
- strict on risky or release-sensitive work

## Decision Filter

Prefer a change when it improves one or more of these:

- clearer skill activation from ambiguous intent
- lower token load by keeping process skills small and self-contained
- better durability of design, plan, and proof artifacts
- stronger evidence before any completion claim
- clearer auditability of current state through `help` and `next`
- safer host adaptation without forking skill semantics

Challenge a change when it mainly adds:

- tool-first navigation that competes with sibling skills
- script surfaces that operators must learn before they can understand Forge
- host-specific storytelling inside the shared public contract
- convenience that weakens invariants or hides missing proof
- more artifacts without clearer decisions or better auditability

## Non-Negotiables

- Apply the 1% rule before any substantive response or action.
- Host-discoverable Forge sibling skills are the primary activation surface.
- Operator/session workflow files are wrappers, not the source of truth.
- `help` and `next` are artifact-backed audit sidecars, not the source of truth.
- Verification language must be earned with fresh proof.
- Python is for invariants, state, and preferences, not the main public operating model.
- Host adapters may improve UX, but they must not fork Forge skill meaning.

## Current Contract Closure

The live contract after the split-skill cutover is intentionally narrow:

- teach natural language first
- teach bootstrap-driven sibling skill activation
- teach process skills before implementation skills
- teach `help` and `next` as readers of durable state
- keep deterministic scripts available for invariants, workflow-state, and preferences
- keep generated host artifacts bootstrap-only and sourced from tracked markdown
- keep release and verification posture explicit without inventing new product surface

## What Changed In This Cutover

- the public story is now skill-first rather than route-preview-first
- `packages/forge-core/skills/*/SKILL.md` is the canonical process source
- `packages/forge-core/workflows/` is operator/session compatibility wrapper surface only
- installing host adapters installs the sibling Forge skill family
- the 1% rule is explicit before any substantive response or action
- `help` and `next` are framed as artifact-backed audit sidecars
- Python is explicitly constrained to invariants, state, preferences, install, and verification
- current docs are responsible for the live contract; historical plans stay historical

## Acceptable Changes Now

- drift correction that keeps docs, overlays, sibling skills, and generated bootstrap artifacts aligned
- compatibility repairs that preserve the current public contract
- stronger invariant checks for workflow-state, preferences, install, or verification
- narrower operator guidance that reduces ambiguity without adding a new product story
- line-budget reductions that keep skills easier to auto-activate

## Escalation Triggers

Escalate into an explicit roadmap or product decision only if:

- the split-skill contract fails to guide real work without falling back to internal scripts as the de facto interface
- `help` or `next` cannot remain artifact-backed sidecars because durable state is too weak or ambiguous
- host adapters need materially different skill meaning to work at all
- current invariant or verification machinery fails to catch contract drift in real use
- a proposed change would expand Forge beyond its current narrow execution-kernel posture

## Deferred Boundary

Keep these deferred unless new evidence forces them back into scope:

- new public route-inspection surfaces
- companion or runtime expansion that makes core less host-neutral
- extra release posture tiers that do not change behavior
- host-rich convenience layers that bypass sibling skills
- analytics or memory systems that compete with workflow-state as the durable execution record

There is no active roadmap tranche now.

Current maintainer guidance lives in `docs/current/*` plus this reference, while historical plans remain historical input only.
