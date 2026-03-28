# Forge Install

## Goal

Install the built bundle from `dist/` into a real runtime instead of editing the live runtime directory directly.
The install flow uses in-place sync so rollout is safer when the host is holding locks on the runtime root.

## Default targets

- `forge-antigravity` -> `~/.gemini/antigravity/skills/forge-antigravity`
- `forge-codex` -> `~/.codex/skills/forge-codex`

`forge-core` has no default target. Pass `--target` explicitly if you need to install it.
`forge-browse` also has no default target. Pass `--target` explicitly for runtime-tool installs.
`forge-design` also has no default target. Pass `--target` explicitly for runtime-tool installs.

## Standard Flow

```powershell
python scripts/verify_repo.py
python scripts/build_release.py
python scripts/install_bundle.py forge-antigravity --build
python scripts/install_bundle.py forge-codex --activate-codex
python scripts/install_bundle.py forge-browse --target C:\tools\forge-browse --register-codex-runtime --register-gemini-runtime
python scripts/install_bundle.py forge-design --target C:\tools\forge-design --register-codex-runtime --register-gemini-runtime
```

If Windows Codex is expected to reply in Vietnamese with full diacritics, run the bundled UTF-8 helper after `--activate-codex`:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME/.codex/skills/forge-codex/scripts/enable_windows_utf8.ps1"
powershell -ExecutionPolicy Bypass -File "$HOME/.codex/skills/forge-codex/scripts/enable_windows_utf8.ps1" -Persist
```

The UTF-8 helper is only needed when preferences explicitly set `language=vi`.

`--activate-codex` is for real Codex rollout:

- sync `forge-codex` into `~/.codex/skills/forge-codex`
- rewrite `~/.codex/AGENTS.md` so `forge-codex` becomes the only global orchestrator
- retire `~/.codex/awf-codex`
- retire legacy global skills matching `~/.codex/skills/awf-*`

## Dry Run

```powershell
python scripts/install_bundle.py forge-antigravity --dry-run
python scripts/install_bundle.py forge-codex --dry-run
python scripts/install_bundle.py forge-codex --dry-run --activate-codex
python scripts/install_bundle.py forge-browse --dry-run --target C:\tools\forge-browse --register-codex-runtime --register-gemini-runtime
python scripts/install_bundle.py forge-design --dry-run --target C:\tools\forge-design --register-codex-runtime --register-gemini-runtime
```

## Safety

- The script automatically backs up the existing runtime into `.install-backups/` before syncing.
- With `--activate-codex`, the script also backs up `~/.codex/AGENTS.md`, the legacy runtime, and any retired legacy skills.
- Use `--backup-dir` to override the backup location.
- Use `--no-backup` only when the target runtime is disposable.
- Do not install anywhere inside the repo tree, including `packages/`, `dist/`, or the repo root.
- The script prunes files that are no longer in the new bundle, but it does not need to delete the entire runtime root.

## Override Target

```powershell
python scripts/install_bundle.py forge-core --target C:\path\to\custom\runtime
python scripts/install_bundle.py forge-antigravity --target C:\path\to\sandbox\forge-antigravity
python scripts/install_bundle.py forge-browse --target C:\path\to\tools\forge-browse --register-codex-runtime
python scripts/install_bundle.py forge-design --target C:\path\to\tools\forge-design --register-gemini-runtime
```
