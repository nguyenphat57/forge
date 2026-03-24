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

> Muc tieu: giu `/recap` va cac bien the quen tay cua Antigravity, nhung van route ve `session` restore mode cua Forge core.

## Process

1. Vao `workflows/execution/session.md` theo restore mode.
2. Repo-first:
   - `git status`
   - docs/plans/specs
   - `.brain` neu can
3. Tra ve summary ngan + next step ro rang.

## Activation Announcement

```text
Forge Antigravity: recap | restore from repo first, memory second
```
