# Backend Briefs

> Dùng khi task backend là medium/large, chạm contract/schema/job/event, hoặc caller impact chưa rõ.

## Why This Exists

`backend` cần một first artifact giống `frontend`, nhưng tập trung vào:

- contract hoặc surface in scope
- validation và authorization boundary
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

Khi task kéo dài hoặc có nhiều API/job/event:

```powershell
python scripts/generate_backend_brief.py "..." --persist --project-name "Example Project" --surface cancel-orders
```

Artifact tạo ra:

```text
.forge-artifacts/backend-briefs/<project-slug>/MASTER.md
.forge-artifacts/backend-briefs/<project-slug>/MASTER.json
.forge-artifacts/backend-briefs/<project-slug>/surfaces/<surface>.md
```

Reading order:
1. `MASTER.md`
2. `surfaces/<surface>.md` nếu surface có override

## Minimum Brief Quality

- Có contract/surface rõ
- Có compatibility và caller impact rõ
- Có note về migration hoặc persistence impact nếu data chạm vào
- Có note về idempotency/retry/replay nếu async hoặc evented
- Có note về observability hoặc rollback risk

## Validate A Persisted Brief

```powershell
python scripts/check_backend_brief.py .forge-artifacts/backend-briefs/<project-slug> --surface cancel-orders
```
