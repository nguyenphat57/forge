# Forge Tooling

> Thin pointer for maintainers. Use `kernel-tooling.md` for the live command surface; use the specialized references below when a narrower artifact contract matters.

## Start Here

- Current maintainer reading path: `reference-map.md`
- Live deterministic command surface: `kernel-tooling.md`
- Host/operator contract catalog: `data/orchestrator-registry.json`
- Generated host artifact inventory: `docs/architecture/host-artifacts-manifest.json`

## Specialized References

- `personalization.md` for preference resolution and durable response-style writes
- `workspace-init.md` for workspace bootstrap and skeleton creation
- `help-next.md` and `run-guidance.md` for operator recovery and command-routing semantics
- `backend-briefs.md` for persisted backend brief artifact validation
- `ui-briefs.md` for persisted UI brief artifact validation
- `ui-progress.md` for long-running frontend or visual-lens progress artifacts

## Historical Boundary

- Runtime-tool, companion-package, preset-overlay, and canary-era command catalogs are not part of the active kernel contract.
- If an older doc still teaches those surfaces, treat it as archive context unless `docs/current/` points to it explicitly.
