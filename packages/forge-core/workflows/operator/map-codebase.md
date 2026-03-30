---
name: map-codebase
type: operator
triggers:
  - user asks what an unfamiliar repo is doing
  - user wants a brownfield summary before edits
quality_gates:
  - Persist a structured project map under .forge-artifacts
  - Distinguish detected facts from open questions
  - Focus mode must not overwrite the full map
---

# Map-Codebase - Brownfield Project Mapping

> Goal: produce a durable project map so later workflows reuse context instead of rediscovering it.

## Process

1. Resolve the workspace root.
2. Run:

```powershell
python scripts/map_codebase.py --workspace <workspace> --format json
```

3. Persist:
   - stack summary
   - architecture summary
   - testing summary
   - integrations
   - risks and open questions

Persisted artifacts:
- `.forge-artifacts/codebase/summary.json`
- `.forge-artifacts/codebase/summary.md`
- `.forge-artifacts/codebase/architecture.md`
- `.forge-artifacts/codebase/testing.md`
- `.forge-artifacts/codebase/focus/<area>.md` when focus mode is used

After running:
- use `plan` if the first slice is still ambiguous
- use `spec-review` when the map shows risky boundaries
- use `build` only after the first coherent slice is named

## Output Contract

```text
Forge Map-Codebase
- Status: PASS
- Workspace: [...]
- Project: [...]
- Stack: [...]
- Next actions:
  - [...]
```
