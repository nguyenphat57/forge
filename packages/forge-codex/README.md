# forge-codex

Codex adapter overlay for Forge.

Contents:

- `SKILL.delta.md` as the canonical Codex-only source
- generated `SKILL.md` as the checked-in merged source artifact
- `AGENTS.example.md` for workspace integration
- `AGENTS.global.md` for taking over the global Codex host entrypoint
- `workflows/execution/dispatch-subagents.md` as a thin compatibility wrapper for `forge-dispatching-parallel-agents`
- `forge-session-management` as the sole owner for resume, save context, and handover
- sibling Forge skills installed next to `forge-codex` for process activation
- thin operator wrappers for natural-language-first `help`, `next`, `run`, and `bump`
- sibling skill `forge-init` for workspace bootstrap and docs normalization
- `codex-operator-surface.md` for the adapter boundary and alias policy

## Windows UTF-8 for Vietnamese

If Codex is expected to speak Vietnamese with full diacritics on Windows, do both:

1. Persist the language setting in adapter-global Forge state:

```powershell
python commands/write_preferences.py --language vi --orthography vietnamese_diacritics --apply
```

`forge-codex` defaults to English. Use workspace `.brain/preferences.json` only for repo-specific overrides that should not become the Codex-wide default.

2. Apply the bundled PowerShell helper in the PowerShell session that will read or write Forge files:

```powershell
.\tools\enable_windows_utf8.ps1
.\tools\enable_windows_utf8.ps1 -Persist
```

Why this matters on Windows PowerShell 5.1:

- `forge-codex` writes UTF-8 without BOM on purpose.
- Console UTF-8 settings alone are not enough; `Get-Content` and other file cmdlets can still decode UTF-8 files with the active ANSI code page unless their default `-Encoding` is also set to UTF-8.
- `enable_windows_utf8.ps1` now sets both console encodings and PowerShell file-cmdlet encoding defaults for the current session; `-Persist` appends the same block to the PowerShell profile.
- If you are inspecting a Forge file before running the helper, use an explicit encoding: `Get-Content -Encoding utf8 -Raw <path>`.

Build output is produced by overlaying adapter files on top of `forge-core`, then materializing the sibling skill pack from `packages/forge-skills/`.

