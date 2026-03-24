# Forge Help/Next

> Mục tiêu: giữ `help` và `next` ở `forge-core` theo kiểu repo-first, host-neutral, và có thể tái sử dụng cho adapter tương lai.

## Core Contract

- Engine canonical: `scripts/resolve_help_next.py`
- Workflow wrappers: `workflows/operator/help.md` và `workflows/operator/next.md`
- Nguồn ưu tiên:
  1. `git status`
  2. `docs/plans/` và `docs/specs/`
  3. `.brain/session.json`
  4. `.brain/handover.md`
  5. `README`

## Stage Model

| Stage | Khi nào |
|------|---------|
| `blocked` | session hoặc handover cho thấy blocker rõ |
| `session-active` | có task đang làm hoặc pending tasks rõ ràng |
| `active-changes` | working tree đang có diff / file mới |
| `planned` | chưa code nhưng đã có plan/spec mới nhất |
| `unscoped` | repo chưa cho thấy một slice đang active |

## Output Contract

- `current_focus`
- `suggested_workflow`
- `recommended_action`
- `alternatives` tối đa 2 mục
- `evidence`
- `warnings`

## Guardrails

- Không nhầm `help/next` thành recap dài dòng.
- Không gợi ý ritual như `/save-brain`.
- Không đưa next step mơ hồ nếu có thể chốt slice cụ thể hơn.
- Khi context yếu, phải nói rõ ràng là repo chưa có enough signals.

## Adapter Boundary

- `forge-antigravity` có thể expose rõ `/help` và `/next`.
- `forge-codex` nên giữ natural-language first và có thể để slash là optional alias.
- Adapter không được fork stage model hay source priority.
