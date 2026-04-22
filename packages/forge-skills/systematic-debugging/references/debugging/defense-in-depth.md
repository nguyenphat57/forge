# Defense-In-Depth Validation

Use this after root-cause tracing proves that invalid data, unsafe state, or a broken invariant crossed more than one layer. The goal is not to scatter checks everywhere; the goal is to make the same class of bug structurally hard to reintroduce.

Core rule: validate at the boundaries that own meaning. A single check is fragile when other entrypoints, tests, mocks, generated artifacts, or host adapters can bypass it.

## When To Load This Reference

- A bug was caused by empty, malformed, stale, or unsafe input.
- A dangerous operation used an unchecked path, command, environment value, state id, or artifact.
- Multiple callers can reach the same lower-level operation.
- A test or host adapter bypassed the intended public entrypoint.
- The fix needs both a source correction and a guard against recurrence.

## Validation Layers

### Layer 1: Entry Boundary

Reject invalid public input as early as possible.

Examples:

- missing workspace path
- unknown workflow state
- invalid artifact location
- unsupported command argument
- unsafe target directory

### Layer 2: Domain Boundary

Validate that the data makes sense for the operation, not just that it exists.

Examples:

- stage transition is legal
- proof matches the claimed state
- generated path belongs to the expected workspace
- selected skill is compatible with the current task

### Layer 3: Dangerous Operation Guard

Protect operations that can corrupt state, pollute the repo, delete files, publish artifacts, or claim completion.

Examples:

- refuse recursive filesystem operations outside the expected root
- refuse merge-ready state with blockers
- refuse ready claims without fresh proof
- refuse worktree operations when the target path is not ignored or isolated

### Layer 4: Diagnostic Breadcrumb

Leave enough context to diagnose future failures without guessing.

Examples:

- include workspace, artifact path, stage, status, command, and verification id in errors
- prefer actionable error messages over silent fallback
- log or report only what explains the boundary failure

## Applying The Pattern

1. Map the data path from entrypoint to failure.
2. Mark every boundary where the data changes meaning or trust level.
3. Choose the minimum checks that make the bug impossible or clearly rejected.
4. Add a regression test for the source fix and one bypass test for the guard when viable.
5. Keep error messages specific enough for the next investigation.

## Avoid Over-Validation

Defense-in-depth is not duplicate boilerplate.

Avoid:

- repeating the same shallow check at every function
- hiding the source bug behind fallback behavior
- converting programmer errors into vague user-facing messages
- accepting bad state and "fixing" it silently

Prefer:

- strict validation at public and trust-crossing boundaries
- invariant checks before irreversible operations
- clear failure when state is impossible
- local recovery only when the recovery behavior is part of the contract

## Forge-Specific Boundaries

Use extra care around:

- workflow-state writes and stage transitions
- proof before completion claims
- preference resolution and personalization state
- worktree paths and `.gitignore` safety
- generated host artifacts
- release, install, rollback, and publish scripts

Pair this with `debugging/root-cause-tracing.md` before deciding which layers need guards.
