# Forge Public Readiness

Date: 2026-04-02
Status: `1.15.0` is the current stable release after the host-aware delegation preference release cut.

## What This Checklist Covers

This checklist is for publishing the Forge monorepo to a public audience without presenting it as broadly proven production software.

## Public Release Gate

- root README explains the release model and current maturity
- contributor, security, and conduct docs exist at the repo root
- canonical repo verification passes with fresh evidence
- public docs do not depend on maintainer-local absolute filesystem paths
- release/install docs point to supported source and bundle flows

## Optional Hardening Items

- keep optional live runtime smoke evidence current for browser-backed flows

## Latest Evidence

- `python scripts/verify_repo.py` passed on 2026-04-02
- release and install flows are documented under `docs/release/`
- final GitHub visibility steps are documented in `docs/release/github-public-switch-checklist.md`
- real-repo canary and authenticated QA evidence is recorded in the 2026-03-29 project reports
- release-facing docs now align on `1.15.0` as the stable source version

## Verdict

Forge `1.15.0` is in a reasonable state for public stable release under the current policy.
The hardening item above is optional evidence, not a release precondition.
