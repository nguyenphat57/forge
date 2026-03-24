# Forge Rollback Guidance

> Dùng khi cần một rollback plan an toàn, không blind-execute.

## Canonical Script

```powershell
python scripts/resolve_rollback.py --scope deploy --customer-impact broad --has-rollback-artifact
python scripts/resolve_rollback.py --scope migration --data-risk high --failure-signal "writes failing after migration"
```

## Contract

- Chốt rollback scope
- Chốt customer impact và data risk
- Chọn strategy an toàn nhất
- Trả về suggested workflow tiếp theo và verification checklist

## Boundary

- Core chỉ lập kế hoạch rollback.
- Adapter có thể thêm UX wrapper, nhưng không được bỏ qua warning data-risk hay rollback-scope gate.
