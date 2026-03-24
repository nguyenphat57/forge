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

> Mục tiêu: chốt một bước tiếp theo cụ thể, ngắn, và an toàn dựa trên repo state hiện tại.

<HARD-GATE>
- Không đưa next step mơ hồ kiểu "tiếp tục làm".
- Không đề xuất scope mới nếu repo state chưa ủng hộ.
- Không đưa hơn 1 next step chính; alternatives chỉ là phụ.
</HARD-GATE>

## Process

1. Inspect workspace state:
   - active plan/spec
   - current working tree changes
   - session hoặc handover artifacts nếu có
2. Resolve bằng:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode next
```

3. Trả về:
   - current focus
   - next step cụ thể
   - tối đa 1-2 alternatives khi cần

## Output Contract

```text
Focus hiện tại: [...]
Next step: [...]
Nếu cần đổi hướng:
- [...]
```

## Activation Announcement

```text
Forge: next | one concrete step from repo state
```
