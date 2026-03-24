# forge-codex

Codex adapter overlay for Forge.

Contents:

- Codex-oriented `SKILL.md`
- `AGENTS.example.md` for workspace integration
- `AGENTS.global.md` for taking over the global Codex host entrypoint
- `workflows/execution/dispatch-subagents.md` for Codex-native multi-agent delegation
- thin operator wrappers for natural-language-first `help`, `next`, `run`, `bump`, `rollback`, `customize`, and `init`
- `codex-operator-surface.md` for the adapter boundary and alias policy

Build output is produced by overlaying these files on top of `forge-core`.
