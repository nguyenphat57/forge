# Forge Architecture Layers

> Goal: keep Forge extensible without mixing orchestration, generated host surfaces, persistent state, and runtime actuators into one layer.

## Canonical Four-Layer Contract

Forge uses four layers:

1. `core`
2. `generated artifacts`
3. `workflow state`
4. `runtime tools`

If a change crosses layers, the change must say so explicitly and preserve the boundary for each layer.

## Layer 1: Core

Core is the reusable engine:

- intent routing
- execution/review/gate workflows
- verification contracts
- shared references and schemas
- deterministic host-neutral scripts

Canonical locations:

- `packages/forge-core/SKILL.md`
- `packages/forge-core/workflows/`
- `packages/forge-core/domains/`
- `packages/forge-core/data/`
- `packages/forge-core/scripts/`

Core must not depend on a single host entry file such as `AGENTS.md` or `GEMINI.md`.

## Layer 2: Generated Artifacts

Generated artifacts are host-facing or release-facing outputs derived from a canonical source:

- global host templates
- host wrapper surfaces
- merged release outputs that must stay reproducible

Canonical rule:

- edit the source, not the generated overlay, unless the change is a deliberate emergency repair and the source is updated in the same change

Current canonical tooling:

- `docs/architecture/host-artifacts-manifest.json`
- `scripts/generate_host_artifacts.py`
- `scripts/host_artifact_specs.py`
- `scripts/host_artifacts_support.py`

Current generated outputs:

- `packages/forge-codex/overlay/AGENTS.global.md`
- `packages/forge-codex/overlay/workflows/execution/session.md`
- `packages/forge-codex/overlay/workflows/operator/help.md`
- `packages/forge-codex/overlay/workflows/operator/next.md`
- `packages/forge-codex/overlay/workflows/operator/run.md`
- `packages/forge-codex/overlay/workflows/operator/bump.md`
- `packages/forge-codex/overlay/workflows/operator/rollback.md`
- `packages/forge-codex/overlay/workflows/operator/customize.md`
- `packages/forge-codex/overlay/workflows/operator/init.md`
- `packages/forge-antigravity/overlay/GEMINI.global.md`

## Layer 3: Workflow State

Workflow state is persistent coordination state, not policy prose:

- execution checkpoints
- chain status
- UI progress
- run reports
- quality-gate decisions

Canonical locations:

- `.forge-artifacts/workflow-state/<project>/latest.json`
- `.forge-artifacts/workflow-state/<project>/events.jsonl`
- `.forge-artifacts/workflow-state/<project>/packet-index.json`
- `packages/forge-core/scripts/workflow_state_support.py`
- `packages/forge-core/scripts/workflow_state_summary.py`

Rules:

- workflow state stores evidence-backed coordination data
- it should be machine-readable first
- it must not become telemetry or product analytics
- packet index is the bounded continuity read model for cheaper packet resume paths
- progressive context loading can summarize packet index first, then expand to full workflow-state only when needed

## Layer 4: Runtime Tools

Runtime tools are concrete actuators that do work beyond routing text:

- browser automation
- design/mockup servers
- future long-lived daemons or external control planes

Rules:

- runtime tools stay outside the core orchestrator
- they may expose Forge-friendly wrappers, but they must not become a second orchestrator
- they need their own install, smoke, and failure model

## Dependency Direction

Allowed defaults:

```text
core -> generated artifacts
core -> workflow state
generated artifacts -> core
runtime tools -> workflow state
```

Disallowed defaults:

```text
generated artifacts -> workflow state
generated artifacts -> host-only logic inside core
runtime tools -> generated artifacts by default
```

## Bounded Extension Surface (1.14.x)

Extension and preset boundaries begin at overlays and end before core semantics:

- packet templates may prefill canonical fields but cannot redefine packet graph or proof gates
- workflow overlays may change wording/entrypoints but cannot change stage status semantics
- planning presets may speed plan authoring but cannot bypass verification or workflow-state requirements

If an extension requires semantic drift, move the proposal into core and update contract tests first.

## Decision Tests

Before adding or moving a capability, ask:

1. Is this reusable policy/engine logic? Put it in `core`.
2. Is this a reproducible host-facing output? Put it in `generated artifacts`.
3. Is this durable machine-readable execution evidence? Put it in `workflow state`.
4. Is this a concrete actuator or daemon? Put it in `runtime tools`.

If the answer is unclear, default to the lower-power layer:

- generated artifacts before adapter hand edits
- workflow state before prose-only recap
- runtime tools outside core before core-internal side effects

## Review Checklist

- the layer of each new file is obvious
- build/verify scripts know how generated artifacts stay fresh
- workflow state remains machine-readable and bounded
- runtime tools remain optional and independently verifiable
- docs and tests point to the same canonical source
