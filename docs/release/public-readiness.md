# Forge Public Readiness

Date: 2026-05-02
Status: `5.4.0` is the current stable release after session continuity gained selective task closeout capture and workspace resume now restores relevant decisions and learnings.

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

- `python -m unittest test_session_context test_contracts` passed from `packages/forge-core/tests` on 2026-05-02
- `python scripts/verify_repo.py` passed on 2026-05-02
- release and install flows are documented under `docs/release/`
- release-facing docs now align on `5.4.0` as the stable source version

## Verdict

Forge `5.4.0` is in a reasonable state for public stable release under the current policy.
The hardening item above is optional evidence, not a release precondition.
