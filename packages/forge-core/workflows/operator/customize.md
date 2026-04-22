---
name: customize
type: compatibility-wrapper
---

# Customize Compatibility Wrapper

Use this file only as a thin compatibility wrapper.

Canonical activation stays natural-language first, `python scripts/repo_operator.py customize --workspace <workspace> --format json`, and host-native `forge-*` skill discovery.

Inspect with `python scripts/resolve_preferences.py --workspace <workspace> --format json` and persist with `python scripts/write_preferences.py ... --apply`.

Keep writes sparse, preserve canonical preference keys, and do not mutate state during read-only inspection.
