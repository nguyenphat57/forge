# forge-antigravity

Antigravity adapter overlay for Forge.

Contents:

- `SKILL.delta.md` as the canonical Antigravity-only source
- generated `SKILL.md` as the checked-in merged source artifact
- `agents/openai.yaml` for host UI metadata
- Operator wrapper workflows for `help`, `next`, `run`, and `bump`
- Sibling skill `forge-init` for workspace bootstrap and docs normalization
- Natural-language session requests for `resume`, `save context`, and `handover`
- Antigravity operator surface reference

The build overlays these files on top of `forge-core`, then composes the shipped `SKILL.md` directly from core shared sections plus `SKILL.delta.md`.
