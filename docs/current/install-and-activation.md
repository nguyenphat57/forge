# Forge Current Install And Activation

## Source repo versus installed runtime

Treat these as different surfaces:

- source repo: edit, test, and verify in this monorepo
- installed runtime: build from `dist/`, then install or activate the real bundle

The source repo uses `scripts/repo_operator.py`.
Installed runtimes keep the bundle-native script and workflow layout.

## Canonical inner loop

```powershell
python scripts/repo_operator.py help --workspace <repo> --format json
python scripts/repo_operator.py next --workspace <repo> --format json
python scripts/verify_repo.py --profile fast
```

## Canonical release/install loop

```powershell
python scripts/verify_repo.py
python scripts/build_release.py
python scripts/install_bundle.py forge-codex --activate-codex
python scripts/install_bundle.py forge-antigravity --activate-gemini
```

## When re-activation is required

Re-activate the installed host only when global template content or installed bundle docs change.

Typical cases:

- `packages/forge-codex/overlay/AGENTS.global.md`
- `packages/forge-antigravity/overlay/GEMINI.global.md`
- installed workflow or reference files that the host reads directly after install

## When re-activation is not required

Do not re-activate a host just because the source repo's local `AGENTS.md` changed.
Repo-local routing changes take effect immediately for source-repo work in this checkout.

## Deferred scope

This tranche does not refactor `install_bundle_host.py` into a new activation architecture.
Behavior stays stable unless a text or template expectation has to change.
