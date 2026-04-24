# Codex Workspace Entry

Forge remains the evidence-first execution kernel for this workspace. This file is only a local augmentation for the source repo.

## Read Order

1. Read this `AGENTS.md`.
2. Keep Forge global rules from the installed `forge-codex` orchestrator.
3. For this source repo, use Forge sibling skills as the canonical public workflow surface before inspecting package internals.

## Source Repo Public Surface

- Use `forge-session-management` for `resume`, `continue`, and recap-style context restore.
- Use `forge-session-management` for `save context`.
- Use `forge-session-management` for `handover`.
- Use natural language plus Forge skills for guidance, next-step selection, and command execution; pair command execution with `forge-verification-before-completion`.
- Use sibling skill `forge-bump-release` for explicit release bump preparation, semver inference, `VERSION` updates, and `CHANGELOG.md` updates.
- Use sibling skill `forge-deploy` for pre-deploy readiness, live deploy execution, post-deploy verification, and rollback guidance.
- Use sibling skill `forge-customize` plus its owner commands for durable preference updates; `customize` is not a repo operator action.
- Use sibling skill `forge-init` for workspace bootstrap, bootstrap docs creation, and docs normalization.
- Keep package-level script paths as implementation detail unless the task is to edit or debug the underlying engine.

## Notes

- Keep this file thin; do not duplicate Forge routing, verification, or workflow semantics here.
- `forge-session-management` resume may auto-seed canonical `workflow-state` from a legacy JSON artifact or the latest plan/spec when no canonical root exists yet.
- Prefer natural-language requests first. Slash commands remain optional aliases.
- `initialize_workspace.py` remains the deterministic engine behind `forge-init`; do not treat it as a public repo operator action.
- `prepare_bump.py` remains the deterministic engine behind `forge-bump-release`; do not treat it as a public repo operator action.
- `forge-deploy` does not own semver, changelog, or PR decisions; keep those with their existing sibling skills.
