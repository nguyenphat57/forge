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
5. Optionally run extra smoke checks for changed runtime surfaces when additional confidence is useful.

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
- `build_release.py` writes `version`, `git_revision`, and `git_tree` into `BUILD-MANIFEST.json`.
- `git_revision` records the source commit at build time.
- `git_tree` records working-tree provenance before release artifacts are materialized.
- `git_tree.available` is `false` when the repo status cannot be read.
- `git_tree.state` is `clean`, `modified`, `untracked`, `mixed`, or `unknown`.
- `git_tree.modified_files` lists tracked paths with local changes.
- `git_tree.untracked_files` lists untracked paths.
- `docs/release/package-matrix.json` defines the default target strategy and required bundle paths for each shipped bundle.
- Source-only example companions stay outside `docs/release/package-matrix.json` and do not need to track the monorepo release version.
- Runtime-tool bundles such as `forge-browse` and `forge-design` ship as direct package copies with their own verify/install path instead of inheriting `forge-core`.
- `install_bundle.py` writes `INSTALL-MANIFEST.json` into the installed runtime.

## Promotion

- Public preview is acceptable after `verify_repo.py` passes, public-facing root docs exist, and public docs have been scrubbed of maintainer-local paths.
- General public release uses the canonical verification gate above; extra runtime evidence is optional hardening, not a release precondition.
- Forge `1.14.0` is the current stable release after the `1.14.0` competitive cut sweep and the latest canonical verification gate both passed.
- `forge-antigravity` is currently the most mature adapter for real rollout.
- `forge-codex` has passed internal verification and is eligible for release under the current policy.
- `forge-codex` host wrappers and global entry files should stay generated from canonical host-artifact sources instead of being maintained by hand.
- `forge-browse` is an optional runtime actuator and now ships with a live smoke path in source, dist, and repo verification.
- `forge-design` is an optional runtime design tool and should ship with persisted brief plus browse-capture smoke in place.
- For Codex host takeover, use `install_bundle.py forge-codex --activate-codex` to rewrite global `AGENTS.md` and retire the legacy runtime in one backed-up step.
- `forge-core` must not absorb host-specific UX just to serve one current adapter.
- Only tag a release after `verify_repo.py` passes.
