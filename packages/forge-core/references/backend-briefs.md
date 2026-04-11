# Backend Briefs

> Use this when the backend task is medium/large, touches contracts, schema, jobs, or events, or has unclear caller impact.

## Why This Exists

Backend implementation needs an initial artifact, just as UI implementation does, but it focuses on:

- contract or surface in scope
- validation and authorization boundary
- data model / migration impact
- consistency / idempotency / retry behavior
- observability / ops notes
- caller / consumer compatibility

## Generate A Backend Brief

### Sync API

```powershell
python scripts/generate_backend_brief.py "Add bulk order cancellation endpoint" `
  --pattern sync-api `
  --runtime node-service `
  --surface cancel-orders
```

### Async Job

```powershell
python scripts/generate_backend_brief.py "Reconcile failed payouts in background worker" `
  --pattern async-job `
  --runtime python-service `
  --surface payout-reconcile
```

### Event Flow

```powershell
python scripts/generate_backend_brief.py "Version order-paid event for downstream inventory" `
  --pattern event-flow `
  --runtime go-service `
  --surface order-paid
```

### Data Change

```powershell
python scripts/generate_backend_brief.py "Split customer table into profile + preferences" `
  --pattern data-change `
  --runtime java-service `
  --surface customer-schema
```

## Persisted Master + Surface Override Pattern

When the task is long or has many APIs/jobs/events:

```powershell
python scripts/generate_backend_brief.py "..." --persist --project-name "Example Project" --surface cancel-orders
```

Generated artifacts:

```text
.forge-artifacts/backend-briefs/<project-slug>/MASTER.md
.forge-artifacts/backend-briefs/<project-slug>/MASTER.json
.forge-artifacts/backend-briefs/<project-slug>/surfaces/<surface>.md
```

Reading order:
1. `MASTER.md`
2. `surfaces/<surface>.md` if the surface has override

## Minimum Brief Quality

- Clear contract or surface definition
- Clear compatibility and caller impact
- A note on migration or persistence impact when data changes
- A note on idempotency/retry/replay for async or evented work
- A note on observability or rollback risk

## Validate A Persisted Brief

```powershell
python scripts/check_backend_brief.py .forge-artifacts/backend-briefs/<project-slug> --surface cancel-orders
```
