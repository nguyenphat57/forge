---
name: recap
type: flexible
triggers:
  - shortcut: /recap
  - shortcut: /recap full
  - shortcut: /recap deep
quality_gates:
  - Repo state is restored before memory files
  - Summary stays scoped and ends with one next step
  - Wrapper does not fork core session restore logic
---

# Recap - Antigravity Restore Wrapper

> Mục tiêu: giữ `/recap` và các biến thể quen tay của Antigravity, nhưng vẫn route về `session` restore mode của Forge core.

## Process

1. Vào `workflows/execution/session.md` theo restore mode.
2. Repo-first:
   - `git status`
   - docs/plans/specs
   - `.brain` nếu cần
3. Trả về summary ngắn + next step rõ ràng.

## Activation Announcement

```text
Forge Antigravity: recap | restore from repo first, memory second
```
