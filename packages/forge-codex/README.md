# forge-codex

Codex adapter overlay for Forge.

Contents:

- Codex-oriented `SKILL.md`
- `AGENTS.example.md` for workspace integration
- `AGENTS.global.md` for taking over the global Codex host entrypoint
- `workflows/execution/dispatch-subagents.md` for Codex-native multi-agent delegation
- thin operator wrappers for natural-language-first `help`, `next`, `run`, `bump`, `rollback`, `customize`, and `init`
- `codex-operator-surface.md` for the adapter boundary and alias policy

## Windows UTF-8 for Vietnamese

If Codex is expected to speak Vietnamese with full diacritics on Windows, do both:

1. Keep a workspace-local language rule in `.brain/preferences.json`, for example:

```json
{
  "language": "vi",
  "orthography": "vietnamese_diacritics",
  "custom_rules": [
    "Always reply to the user in Vietnamese with full diacritics.",
    "Never use accent-stripped Vietnamese in comments, plans, summaries, or reviews.",
    "If shell or file text appears mojibake, treat it as an encoding issue and restate it in UTF-8 Vietnamese."
  ]
}
```

2. Run the bundled PowerShell helper so the shell itself stays on UTF-8:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/enable_windows_utf8.ps1
powershell -ExecutionPolicy Bypass -File scripts/enable_windows_utf8.ps1 -Persist
```

Build output is produced by overlaying these files on top of `forge-core`.
