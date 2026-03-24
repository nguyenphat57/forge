---
name: next
type: flexible
triggers:
  - shortcut: /next
  - user asks for the next best action
quality_gates:
  - Next step is concrete and anchored to repo state
  - Recommendation does not expand scope
  - Fallback stays actionable when context is weak
---

# Next - Concrete Next-Step Navigator

> Muc tieu: chot mot buoc tiep theo cu the, ngan, va an toan dua tren repo state hien tai.

<HARD-GATE>
- Khong dua next step mo ho kieu "tiep tuc lam".
- Khong de xuat scope moi neu repo state chua ung ho.
- Khong dua hon 1 next step chinh; alternatives chi la phu.
</HARD-GATE>

## Process

1. Inspect workspace state:
   - active plan/spec
   - current working tree changes
   - session or handover artifacts neu co
2. Resolve bang:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode next
```

3. Tra ve:
   - current focus
   - next step cu the
   - toi da 1-2 alternatives khi can

## Output Contract

```text
Focus hien tai: [...]
Next step: [...]
Neu can doi huong:
- [...]
```

## Activation Announcement

```text
Forge: next | one concrete step from repo state
```
