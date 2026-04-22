# Forge Current Install And Activation

## Goal

Describe the current install and activation contract after the split-skill markdown cutover.

## Product Line

- Forge still builds the three kernel bundles: `forge-core`, `forge-codex`, and `forge-antigravity`.
- Installing `forge-codex` or `forge-antigravity` also installs the sibling Forge skill family from `packages/forge-skills/`.
- `forge-core` owns the host-neutral bootstrap, operator/session compatibility wrappers, and invariant tooling.
- `packages/forge-skills/` owns the canonical sibling skill sources that host installs materialize.
- Host bundles add bootstrap files, wrapper language, host-specific access mapping, and shared-script access without forking skill meaning.

## Activation Model

- Installation should produce a host bootstrap that points operators to host-native Forge sibling skills.
- Activation is successful when the host can:
  - restore durable preferences when available
  - apply the 1% rule before substantive responses or actions
  - invoke the matching sibling skill before exploration, clarification, implementation, or completion claims
  - keep process skills before implementation skills
  - preserve evidence-before-claims behavior
- Generated host artifacts remain bootstrap-only. Canonical skill wording belongs in tracked markdown sources, not hand-edited generated files.

## Source Repo Versus Installed Runtime

- Source repo docs under `docs/current/`, `docs/architecture/`, and owner-local companion folders are the canonical maintainer explanation layer.
- Installed runtime artifacts are distribution outputs and should stay aligned with those sources.
- Installed sibling skills are lightweight markdown entrypoints. Shared scripts, data, and state machinery stay in the installed orchestrator bundle.
- If installed wrappers drift from source markdown, fix the source markdown and generation path rather than teaching the generated wrapper as canonical.

## Preferences And State

- Durable preferences stay on the canonical preferences path for the active host or workspace scope.
- Preference resolution and writes remain Python-backed because they are stateful invariant work.
- workflow-state persistence and projection also remain deterministic script territory.
- Those scripts support activation and audit, but they do not replace sibling skills as the public control plane.

## Operator-Facing Outcomes After Install

The first operator-visible story should be:

- Forge is natural-language first.
- Forge is markdown-first and skill-first.
- If a Forge skill may apply, load it first.
- `help` and `next` audit durable artifacts; they do not invent process state.

The first operator-visible story should not be:

- start with `route_preview`
- learn internal deterministic scripts before understanding the skill contract
- treat generated host wrappers as the canonical source of truth
- treat `workflows/` files as the primary activation surface

## Current Non-Changes

- Install safety, backup behavior, and release verification remain intact.
- Bundle fingerprints and release packaging stay canonical.
- Python remains in place for invariants, state, and preferences.
- Operator/session wrappers remain thin compatibility entrypoints where needed.

## Maintainer Guardrails

- Keep install docs aligned with the split-skill public contract.
- Reject changes that make activation more tool-first or host-specific unless they are required for invariant enforcement or state correctness.
- When in doubt, teach the sibling skill and artifact model first, then mention deterministic scripts as support machinery.
