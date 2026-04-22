---
name: build
type: compatibility-wrapper
canonical_skill: forge-executing-plans
---

# Build Compatibility Wrapper

Use host-native skill discovery to invoke `forge-executing-plans`.

This file exists for `/code` and legacy workflow paths only. It is not the implementation source of truth.

Before behavior-changing code, invoke `forge-test-driven-development` when a viable harness exists.

For dirty repos or isolated plan execution, invoke `forge-using-git-worktrees`.

For independent plan tasks, consider `forge-subagent-driven-development` or `forge-dispatching-parallel-agents`.

Before any completion claim, invoke `forge-verification-before-completion`.
