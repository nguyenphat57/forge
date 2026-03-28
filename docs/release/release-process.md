# Forge Release Process

## Source of Truth

- Only edit `packages/forge-core`, adapter overlays, and standalone runtime packages.
- `dist/` is the release artifact.
- Installed runtimes are not development surfaces.

## Release Gate

1. Update source in the monorepo.
2. Run `python scripts/verify_repo.py`.
   This gate now includes the repo secret scan.
3. Build artifacts with `python scripts/build_release.py`.
4. Install or publish from `dist/`.
5. Run host-specific smoke or canary checks before broad promotion.

## Core Purity Gate

Every change that touches `packages/forge-core` must answer:

1. Would this still make sense for a future adapter such as `forge-claude`?
2. Does it depend on `GEMINI.md`, `AGENTS.md`, slash grammar, or any host-specific metadata?
3. Which part is shared engine behavior, and which part is host wrapper behavior?
4. Are we pulling one host's compatibility UX into core?

If a change only fits one host, keep it in that adapter.
The canonical boundary policy lives in `docs/architecture/adapter-boundary.md`.

## Versioning

- The canonical version lives in `VERSION`.
- `build_release.py` writes `version` and `git_revision` into `BUILD-MANIFEST.json`.
- `docs/release/package-matrix.json` defines the default target strategy and required bundle paths for each shipped bundle.
- Runtime-tool bundles such as `forge-browse` and `forge-design` ship as direct package copies with their own verify/install path instead of inheriting `forge-core`.
- `install_bundle.py` writes `INSTALL-MANIFEST.json` into the installed runtime.

## Promotion

- `forge-antigravity` is currently the most mature adapter for real rollout.
- `forge-codex` has passed internal verification, but broad rollout still needs soak time on a real Codex host.
- `forge-codex` host wrappers and global entry files should stay generated from canonical host-artifact sources instead of being maintained by hand.
- `forge-browse` is an optional runtime actuator and now ships with a live smoke path in source, dist, and repo verification.
- `forge-design` is an optional runtime design tool and should ship with persisted brief plus browse-capture smoke in place.
- For Codex host takeover, use `install_bundle.py forge-codex --activate-codex` to rewrite global `AGENTS.md` and retire the legacy runtime in one backed-up step.
- `forge-core` must not absorb host-specific UX just to serve one current adapter.
- Only tag a release after `verify_repo.py` passes.
