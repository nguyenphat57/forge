---
name: bump
type: flexible
triggers:
  - shortcut: /bump
  - user explicitly asks for a version bump or release prep
quality_gates:
  - User-requested only: do not treat generic wrap-up as a bump request
  - Current version is stated and target version is either explicit or justified by inference
  - Wrapper stays thin on top of core bump prep
---

# Bump - Antigravity Operator Wrapper

> Goal: keep `/bump` clear for Antigravity users, while semver math and the release checklist still go through core.

## Process

1. If the user has not specified a bump level, infer from the repo diff and state the reasoning briefly.
2. Preview or apply using:

```powershell
python scripts/prepare_bump.py --workspace <workspace>
python scripts/prepare_bump.py --workspace <workspace> --bump minor
python scripts/prepare_bump.py --workspace <workspace> --bump 1.3.0 --apply --release-ready
```

3. Summarize:
   - version `old -> new`
   - bump source: explicit or inferred
   - files changed
   - next verification step

## Activation Announcement

```text
Forge Antigravity: bump | release prep with explicit or inferred semver
```
