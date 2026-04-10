# Codex Workspace Entry

Forge remains the process-first orchestrator for this workspace. This file is only a local augmentation for the source repo so Codex can use the fastest operator entrypoints immediately.

## Read Order

1. Read this `AGENTS.md`.
2. Keep Forge global rules from the installed `forge-codex` orchestrator.
3. For this source repo, prefer repo-root operator wrappers under `scripts/` before inspecting package internals.

## Source Repo Operator Surface

- Treat `scripts/*.py` at the repo root as the canonical development entrypoints for operator flows in this workspace.
- If a documented root wrapper exists, run it first instead of searching `packages/forge-core/scripts/`.
- Use `python scripts/session_context.py resume --workspace C:\Users\Admin\.gemini\forge --format json` for `resume`, `continue`, and recap-style context restore.
- Use `python scripts/session_context.py save --workspace C:\Users\Admin\.gemini\forge --format json` for `save context`.
- Use `python scripts/session_context.py save --workspace C:\Users\Admin\.gemini\forge --write-handover --format json` for `handover`.
- Use `python scripts/resolve_help_next.py --workspace C:\Users\Admin\.gemini\forge --mode help` for `help`.
- Use `python scripts/resolve_help_next.py --workspace C:\Users\Admin\.gemini\forge --mode next` for `next`.
- Use `python scripts/run_with_guidance.py --workspace C:\Users\Admin\.gemini\forge --timeout-ms 20000 -- <command>` for `run`.
- Use `python scripts/prepare_bump.py --workspace C:\Users\Admin\.gemini\forge <version|major|minor|patch>` for `bump`.
- Use `python scripts/resolve_rollback.py --workspace C:\Users\Admin\.gemini\forge --scope <scope>` for `rollback`.
- Use `python scripts/resolve_preferences.py --workspace C:\Users\Admin\.gemini\forge --format json` plus `python scripts/write_preferences.py --workspace C:\Users\Admin\.gemini\forge ...` for `customize`.
- Use `python scripts/initialize_workspace.py --workspace C:\Users\Admin\.gemini\forge` for `init`.
- Keep package-level script paths as implementation detail unless the task is to edit or debug the underlying engine.

## Notes

- Keep this file thin; do not duplicate Forge routing, verification, or workflow semantics here.
- Prefer natural-language requests first. Slash commands remain optional aliases.
