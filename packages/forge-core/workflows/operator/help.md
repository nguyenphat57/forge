---
name: help
type: compatibility-wrapper
---

# Help Compatibility Wrapper

Use this file only as a thin compatibility wrapper.

Canonical activation stays natural-language first, `python scripts/repo_operator.py help --workspace <workspace> --format json`, and host-native `forge-*` skill discovery.

Read repo state through `python commands/resolve_help_next.py --workspace <workspace> --mode help`.

Return one primary recommendation, at most two alternatives, and do not fabricate current state.

