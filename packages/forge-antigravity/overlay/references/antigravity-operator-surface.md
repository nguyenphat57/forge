# Antigravity Operator Surface

## Primary Surfaces

| Surface | Wrapper | Core contract |
|---------|---------|---------------|
| `/help` | `workflows/operator/help.md` | `scripts/resolve_help_next.py --mode help` |
| `/next` | `workflows/operator/next.md` | `scripts/resolve_help_next.py --mode next` |
| `/run` | `workflows/operator/run.md` | `scripts/run_with_guidance.py` |
| `/bump` | `workflows/operator/bump.md` | `scripts/prepare_bump.py` |
| `/rollback` | `workflows/operator/rollback.md` | `scripts/resolve_rollback.py` |
| `/customize` | `workflows/operator/customize.md` | `scripts/resolve_preferences.py` + `scripts/write_preferences.py` |
| `/init` | `workflows/operator/init.md` | `scripts/initialize_workspace.py` |

## Session Ergonomics

| Alias | Wrapper | Core contract |
|-------|---------|---------------|
| `/recap` | `workflows/operator/recap.md` | `workflows/execution/session.md` restore mode |
| `/save-brain` | `workflows/operator/save-brain.md` | `workflows/execution/session.md` save mode |
| `/handover` | `workflows/operator/handover.md` | `workflows/execution/session.md` handover mode |

## Compatibility Rule

- Wrapper docs co the doi cach trinh bay cho operator-friendly hon.
- Core semantics, schema, va deterministic scripts khong duoc fork.
- Alias chi ton tai de giam friction migration tu AWF/Antigravity cu, khong tao intent moi.
