# Forge Public Readiness

Date: 2026-04-11
Status: `2.1.0` is the current stable release after the thin-SKILL refactor release cut.

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

- `python scripts/verify_repo.py --profile fast` passed on 2026-04-11
- release and install flows are documented under `docs/release/`
- final GitHub visibility steps are documented in `docs/release/github-public-switch-checklist.md`
- real-repo canary and authenticated QA evidence is recorded in the 2026-03-29 project reports
- release-facing docs now align on `2.1.0` as the stable source version

## Verdict

Forge `2.1.0` is in a reasonable state for public stable release under the current policy.
The hardening item above is optional evidence, not a release precondition.
