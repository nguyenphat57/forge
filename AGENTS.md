# Codex Workspace Entry

Forge remains the evidence-first execution kernel for this workspace. This file is only a local augmentation for the source repo so Codex can use the remaining source operator entrypoint immediately.

## Read Order

1. Read this `AGENTS.md`.
2. Keep Forge global rules from the installed `forge-codex` orchestrator.
3. For this source repo, use `scripts/repo_operator.py` as the canonical operator entrypoint before inspecting package internals.

## Source Repo Operator Surface

- Treat `python scripts/repo_operator.py <action> ...` as the canonical development surface for remaining source-repo operator flows in this workspace.
- Use `forge-session-management` for `resume`, `continue`, and recap-style context restore.
- Use `forge-session-management` for `save context`.
- Use `forge-session-management` for `handover`.
- Use natural language plus Forge skills for guidance, next-step selection, and command execution; pair command execution with `forge-verification-before-completion`.
- Use `python scripts/repo_operator.py bump --workspace C:\Users\Admin\.gemini\forge <version|major|minor|patch>` for `bump`.
- Use sibling skill `forge-customize` plus `commands/resolve_preferences.py` and `commands/write_preferences.py` for durable preference updates; `customize` is not a repo operator action.
- Use sibling skill `forge-init` for workspace bootstrap, bootstrap docs creation, and docs normalization.
- Keep package-level script paths as implementation detail unless the task is to edit or debug the underlying engine.

## Notes

- Keep this file thin; do not duplicate Forge routing, verification, or workflow semantics here.
- `forge-session-management` resume may auto-seed canonical `workflow-state` from a legacy JSON artifact or the latest plan/spec when no canonical root exists yet.
- Prefer natural-language requests first. Slash commands remain optional aliases.
- `initialize_workspace.py` remains the deterministic engine behind `forge-init`; do not treat it as a public repo operator action.
