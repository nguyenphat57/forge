---
name: forge-bump-release
description: Use when the user explicitly asks to bump a version, prepare release artifacts, infer semantic version level, update VERSION or CHANGELOG.md, or surface release verification without claiming release-ready.
---

# Forge Bump Release

<EXTREMELY-IMPORTANT>
Use this only for explicit version bump or release-prep requests.

Do not treat generic wrap-up, merge readiness, or task completion as a bump request.
</EXTREMELY-IMPORTANT>

## Overview

Prepare release version changes while keeping semver inference, release artifacts, and verification evidence explicit.

**Core principle:** `VERSION` and root `CHANGELOG.md` edits are release artifacts, not proof that a release is ready. If `CHANGELOG.md` is missing, create it as part of the bump; do not create plural or misspelled variants.

## Required Contract

- Current version is stated and target version is either explicit or justified by inference.
- Bump source is reported as explicit or inferred.
- Low-confidence inference warnings are surfaced.
- Changed files and verification commands are shown.
- Missing root `CHANGELOG.md` is created with the target version entry.
- No commit, push, tag, publish, or release-ready claim is made by this skill alone.

## Process

1. Read [references/bump-release.md](references/bump-release.md) for command details and output expectations.
2. If the user gives `patch`, `minor`, `major`, or an explicit semver, treat the bump source as explicit.
3. If the user asks to choose the level, infer with `auto` and report the script's reasons and confidence.
4. Preview first unless the user explicitly asked to apply.
5. Use the bundled script:

```powershell
python references/scripts/prepare_bump.py --workspace <workspace> --format json
python references/scripts/prepare_bump.py --workspace <workspace> --bump minor --apply --release-ready
```

6. After apply, inspect the diff and run the listed verification commands before any readiness wording.

## Quick Reference

| User asks | Use |
|---|---|
| "Bump patch" | `--bump patch` |
| "Prepare release, choose level" | omit `--bump` or use `--bump auto` |
| "Bump to 2.0.0" | `--bump 2.0.0` |
| "Apply it" | add `--apply` |
| "Release-ready?" | add `--release-ready`, then run returned verification |

## Common Mistakes

- Using retired `repo_operator.py bump` instead of this skill's bundled script.
- Applying a bump without reporting semver source and target version.
- Creating `CHANGELOGS.md`, `CHANGELOS.md`, or `docs/CHANGELOG.md` instead of root `CHANGELOG.md`.
- Hiding low-confidence `auto` inference warnings.
- Saying a release is ready before running fresh verification.
- Committing, pushing, tagging, or publishing from the bump script output alone.

## Integration

- Called by: explicit natural-language version bump and release-prep requests.
- Calls next: `forge-verification-before-completion` before any ready, release-ready, mergeable, or deployable claim.
- Pairs with: `forge-finishing-a-development-branch` when verified release artifacts need branch, PR, merge, or discard decisions.
