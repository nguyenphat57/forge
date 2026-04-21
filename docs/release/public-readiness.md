# Forge Public Readiness

Date: 2026-04-21
Status: `2.9.0` is the current stable release after the flat-build-routing release sync and the latest verification gate.

## What This Checklist Covers

This checklist is for publishing the Forge monorepo to a public audience without presenting it as broadly proven production software.

## Public Release Gate

- root README explains the release model and current maturity
- contributor, security, and conduct docs exist at the repo root
- canonical repo verification passes with fresh evidence
- public docs do not depend on maintainer-local absolute filesystem paths
- release/install docs point to supported source and bundle flows
- current maintainer docs and historical archive boundaries are explicit

## Optional Hardening Items

- keep optional host-backed smoke evidence current for changed adapter flows

## Latest Evidence

- `python -m unittest discover -s packages/forge-core/tests -v` passed on 2026-04-21
- `python packages/forge-codex/overlay/tests/test_adapter_locales.py` passed on 2026-04-21
- `python packages/forge-antigravity/overlay/tests/test_adapter_locales.py` passed on 2026-04-21
- `python scripts/verify_repo.py --profile fast` passed on 2026-04-21
- release and install flows are documented under `docs/release/`
- final GitHub visibility steps are documented in `docs/release/github-public-switch-checklist.md`
- real-repo canary and authenticated QA evidence is recorded in the 2026-03-29 project reports
- release-facing docs now align on `2.9.0` as the stable source version

## Verdict

Forge `2.9.0` is in a reasonable state for public stable release under the current policy.
The hardening item above is optional evidence, not a release precondition.
