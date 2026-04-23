# Backend Briefs

> Use this file when the repo already contains persisted backend brief artifacts and the task needs to validate or interpret them. Forge no longer ships the older backend brief generator as part of the current kernel-only surface.

## Why This Still Exists

Persisted backend briefs remain useful when a repo already tracks them for:

- contract or surface scope
- validation and authorization boundaries
- data model or migration impact
- consistency, idempotency, and retry behavior
- observability and rollback notes
- caller and consumer compatibility

This file documents the artifact shape and current checker behavior. It does not define an active generator flow.

## Expected Artifact Shape

Historical or repo-local backend brief artifacts typically follow:

```text
.forge-artifacts/backend-briefs/<project-slug>/MASTER.md
.forge-artifacts/backend-briefs/<project-slug>/MASTER.json
.forge-artifacts/backend-briefs/<project-slug>/surfaces/<surface>.md
```

Reading order:
1. `MASTER.md`
2. `surfaces/<surface>.md` when the surface has an override

## Minimum Brief Quality

- clear contract or surface definition
- explicit caller impact and compatibility notes
- migration or persistence notes when data changes
- idempotency, retry, or replay notes for async work
- observability or rollback notes

## Validate A Persisted Brief

```powershell
python commands/check_backend_brief.py .forge-artifacts/backend-briefs/<project-slug> --surface cancel-orders
```

## Historical Note

- Older Forge versions shipped backend brief generators. The current kernel-only line keeps only the checker for already-persisted artifacts.
- If a repo needs a brand-new backend brief, create it as a repo-local artifact or from a future roadmap tranche; it is not part of the current shipped tooling surface.

