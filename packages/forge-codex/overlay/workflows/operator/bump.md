---
name: bump
type: flexible
triggers:
  - explicit request to bump version or prepare a release
  - optional alias: /bump
quality_gates:
  - User-requested only: do not treat generic wrap-up as a bump request
  - Current version is stated and target version is either explicit or justified by inference
  - Release verification steps are surfaced
  - Wrapper does not hide core semver/change checklist
---

# Bump - Codex Operator Wrapper

> Goal: keep the bump flow short and clear for the Codex, but still follow the core's user-requested + justified semver contract.

## Process

1. If the user has not stated the bump level, infer from the diff repo and briefly state the reason.
2. Preview/apply using core planner:

```powershell
python scripts/prepare_bump.py --workspace <workspace>
python scripts/prepare_bump.py --workspace <workspace> --bump minor
python scripts/prepare_bump.py --workspace <workspace> --bump minor --apply --release-ready
```

3. Short answer:
   - version from -> to
   - bump source: explicit hay inferred
   - file changed
   - Which verification must be run?

## Activation Announcement

```text
Forge Codex: bump | release change with explicit or inferred semver
```
