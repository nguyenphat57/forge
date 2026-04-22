# Forge Customize Trigger Alignment Design

## Goal

Bring `skills/forge-customize/SKILL.md` in line with the trigger-first writing-skills conventions without losing the Forge-specific operator guidance that makes the skill useful.

## Scope

- Rewrite the skill frontmatter description so it is trigger-based and discovery-friendly.
- Restructure the skill body around trigger-first sections:
  - `Overview`
  - `When to Use`
  - `Quick Reference`
  - `Implementation`
  - `Common Mistakes`
  - `References`
- Keep the existing Forge command guidance and canonical field mapping.
- Strengthen `tests/test_public_customize_skill.py` so the current drift is caught automatically.

## Non-Goals

- Do not add new Forge preference fields.
- Do not invent host-specific behavior that is not already documented in the reference files.
- Do not build a full pressure-scenario harness in this pass.

## Approach

1. Update the skill test first so the current document fails on the missing trigger-alignment requirements.
2. Rewrite the skill to satisfy the stricter contract while staying concise.
3. Run the targeted skill test to verify the new contract passes.

## Verification

- `python tests/test_public_customize_skill.py`
