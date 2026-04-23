# Constitution-Lite

Use this when a repo needs a few durable engineering rules without introducing a new workflow or a heavy config format.

## Shape

Forge treats constitution-lite as a continuity decision:

```powershell
python commands/capture_continuity.py "Testing rules stay strict for checkout flows" --kind decision --scope checkout --tag constitution-lite --evidence docs/current/target-state.md
```

This keeps the rule in:

```text
.brain/decisions.json
```

## Good Rules

- testing: which changes require RED first
- compatibility: what consumers or version windows must be preserved
- simplicity: what complexity is explicitly out of bounds
- review: which lane must sign off before merge

## Rules For Use

- keep the rule short and specific
- scope it to a subsystem, not the whole universe
- attach evidence when the rule came from an incident, spec, or review
- add `revisit_if` when the rule should expire or be reconsidered

## Why This Shape

- no extra artifact type to maintain
- session resume already knows how to read continuity items
- repo-local principles stay opt-in instead of becoming init ceremony

