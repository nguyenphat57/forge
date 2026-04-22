---
name: dispatch-subagents
type: compatibility-wrapper
canonical_skill: forge-dispatching-parallel-agents
---

# Dispatch Subagents Compatibility Wrapper

Use host-native skill discovery to invoke `forge-dispatching-parallel-agents`.

This file exists for `/delegate` and legacy dispatch workflow paths only.

Invoke `forge-dispatching-parallel-agents` when two or more independent tasks can run in parallel.

Invoke `forge-subagent-driven-development` when a written plan should be split into worker or reviewer lanes.

Use `forge-using-git-worktrees` first when repo isolation is needed before parallel work.

Codex-native `spawn_agent` remains an execution aid, not a separate routing policy.
