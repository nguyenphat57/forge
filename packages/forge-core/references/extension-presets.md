# Forge Extension And Preset Boundary

> Goal: keep extension leverage bounded so Forge stays a focused execution kernel and orchestration system instead of turning into plugin sprawl.

## Allowed Surface For 1.14.x

Use extensions/presets only for bounded overlays:

- packet templates: pre-filled packet fields for repeatable slices
- workflow overlays: host/local wrapper text that preserves stage semantics
- planning presets: reusable planning scaffolds for common repo patterns

These overlays can improve speed, but they cannot replace core contract fields.
They cannot override core verification or workflow-state semantics.

## Hard Boundaries

Extensions and presets must not:

- change proof-before-claims or verification gates
- redefine canonical packet graph fields
- bypass workflow-state persistence
- invent a second memory backbone parallel to workflow-state
- force host-specific behavior into `forge-core`

## Ownership Split

- `forge-core` owns canonical semantics and validation.
- adapters own host wording and optional aliases.
- local/workspace overlays own repo-specific convenience only.

If an extension needs to change canonical semantics, the change belongs in core first.

## Example Preset Artifact

Tracked example path:

- `references/examples/example-fast-lane-packet.json`

The artifact is illustrative only. It demonstrates where a preset starts and where core validation still applies.

## Review Checklist

- preset adds speed but does not remove required evidence
- packet template still emits canonical packet fields
- overlay docs point back to core references (`target-state.md`, `architecture-layers.md`, `build.md`, `help-next.md`)
- contract tests cover boundary behavior
