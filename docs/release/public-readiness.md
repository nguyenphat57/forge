# Forge Public Readiness

Date: 2026-04-24
Status: `5.2.0` is the current stable release after generated host artifacts, install and render contracts, and owner-command guidance moved preference resolver references to sibling skill `forge-customize`.

## What This Checklist Covers

This checklist is for publishing the Forge monorepo to a public audience without presenting it as broadly proven production software.

## Public Release Gate

- root README explains the release model and current maturity
- contributor, security, and conduct docs exist at the repo root
- canonical repo verification passes with fresh evidence
- public docs do not depend on maintainer-local absolute filesystem paths
- release/install docs point to supported source and bundle flows
- current maintainer docs do not depend on pre-`2.15.0` plans, specs, audits, or archived references

## Optional Hardening Items

- keep optional host-backed smoke evidence current for changed adapter flows

## Latest Evidence

- `pytest tests/test_host_artifact_generation.py tests/release_repo_test_overlays.py tests/test_install_bundle_codex_host.py tests/test_install_bundle_antigravity_host.py -q` passed on 2026-04-24
- `python scripts/verify_repo.py --profile fast --format json` passed on 2026-04-24
- release and install flows are documented under `docs/release/`
- release-facing docs now align on `5.2.0` as the stable source version

## Verdict

Forge `5.2.0` is in a reasonable state for public stable release under the current policy.
The hardening item above is optional evidence, not a release precondition.
