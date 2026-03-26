---
name: bump
type: flexible
triggers:
  - shortcut: /bump
  - user explicitly asks for a version bump or release prep
quality_gates:
  - User-requested only: do not treat generic wrap-up as a bump request
  - Current version is stated and target version is either explicit or justified by inference
  - Verification commands are surfaced before any release claim
---

# Bump - Version Preparation

> Objective: finalize `old -> new`, update necessary artifact checklist release, and provide a clear verification.

<HARD-GATE>
- Do not bump version if the user has not clearly stated the need to bump/release.
- Do not claim release-ready just because `VERSION` has been changed.
- Do not commit/push automatically if the user has not requested it.
</HARD-GATE>

## Process

1. Determine workspace release and bump level.
   If the user has not stated `major|minor|patch`, infer from git diff since the last change to `VERSION` and state the reason.
2. Preview or apply using:

```powershell
python scripts/prepare_bump.py --workspace <workspace>
python scripts/prepare_bump.py --workspace <workspace> --bump minor
python scripts/prepare_bump.py --workspace <workspace> --bump 1.3.0 --apply --release-ready
```

3. Returns:
   - current version
   - target version
   - bump source: explicit or conveyed
   - inference reasons / confidence if using auto
   - files will change
   - verification commands need to be run

## Output Contract

```text
Version: [... ->...]
Bump source: [explicit|inferred]
Files changed: [...]
Verify continued: [...]
```

## Activation Announcement

```text
Forge: bump | release prep with explicit or inferred semver
```
