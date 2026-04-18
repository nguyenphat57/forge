# forge-codex

Codex adapter overlay for the Forge execution kernel and orchestration system.

Contents:

- `SKILL.delta.md` as the canonical Codex-only source
- generated `SKILL.md` as the checked-in merged source artifact
- `AGENTS.example.md` for workspace integration
- `AGENTS.global.md` for taking over the global Codex host entrypoint
- `workflows/execution/dispatch-subagents.md` for Codex-native multi-agent delegation
- thin operator wrappers for natural-language-first `help`, `next`, `run`, `bump`, `rollback`, `customize`, and `init`
- `codex-operator-surface.md` for the adapter boundary and alias policy

## Windows UTF-8 for Vietnamese

If Codex is expected to speak Vietnamese with full diacritics on Windows, do both:

1. Persist the language setting in adapter-global Forge state:

```powershell
python scripts/write_preferences.py --language vi --orthography vietnamese_diacritics --apply
```

`forge-codex` defaults to English. Use workspace `.brain/preferences.json` only for repo-specific overrides that should not become the Codex-wide default.

2. Run the bundled PowerShell helper so the shell itself stays on UTF-8:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/enable_windows_utf8.ps1
powershell -ExecutionPolicy Bypass -File scripts/enable_windows_utf8.ps1 -Persist
```

Build output is produced by overlaying adapter files on top of `forge-core`, then composing the shipped `SKILL.md` directly from core shared sections plus `SKILL.delta.md`.
