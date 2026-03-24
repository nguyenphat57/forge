# Forge Help/Next

> Muc tieu: giu `help` va `next` o `forge-core` theo kieu repo-first, host-neutral, va co the reuse cho adapter tuong lai.

## Core Contract

- Engine canonical: `scripts/resolve_help_next.py`
- Workflow wrappers: `workflows/operator/help.md` va `workflows/operator/next.md`
- Nguon uu tien:
  1. `git status`
  2. `docs/plans/` va `docs/specs/`
  3. `.brain/session.json`
  4. `.brain/handover.md`
  5. `README`

## Stage Model

| Stage | Khi nao |
|------|---------|
| `blocked` | session hoac handover cho thay blocker ro |
| `session-active` | co task dang lam hoac pending tasks ro rang |
| `active-changes` | working tree dang co diff / file moi |
| `planned` | chua code nhung da co plan/spec moi nhat |
| `unscoped` | repo chua cho thay mot slice dang active |

## Output Contract

- `current_focus`
- `suggested_workflow`
- `recommended_action`
- `alternatives` toi da 2 muc
- `evidence`
- `warnings`

## Guardrails

- Khong nham `help/next` thanh recap dai dong.
- Khong goi y ritual nhu `/save-brain`.
- Khong dua next step mo ho neu co the chot slice cu the hon.
- Khi context yeu, phai noi ro rang la repo chua co enough signals.

## Adapter Boundary

- `forge-antigravity` co the expose ro `/help` va `/next`.
- `forge-codex` nen giu natural-language first va co the de slash la optional alias.
- Adapter khong duoc fork stage model hay source priority.
