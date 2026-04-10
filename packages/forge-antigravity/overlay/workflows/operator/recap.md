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

> Goal: keep `/recap` and its variants familiar for Antigravity users while still routing to Forge core `session` restore mode.
> Deprecated compatibility alias for one stable line. Prefer natural-language `resume` requests.

## Process

1. Enter `workflows/execution/session.md` in restore mode.
2. Repo-first:
   - `git status`
   - docs/plans/specs
   - `.brain` if needed
3. Return a concise summary + one clear next step.
4. Emit a deprecation warning that points users to natural-language `resume` instead of `/recap`.

## Activation Announcement

```text
Forge Antigravity: recap | restore from repo first, memory second
```
