# Forge Solo-Dev Shipping Quickstart

Date: 2026-03-28
Status: current quickstart, aligned to the 2026-03-29 process-first thesis
Audience: one solo developer who wants a dependable path from repo onboarding to release checks

## 1. Start With Core Diagnosis

Run:
- `python packages/forge-core/scripts/doctor.py --workspace <repo> --format text`
- `python packages/forge-core/scripts/map_codebase.py --workspace <repo> --format text`

What this gives you:
- environment and runtime health
- matched optional companion summary when relevant
- active operator profile and verification pack when a confident optional companion match applies
- a durable brownfield map under `.forge-artifacts/codebase/`

## 2. Decide Whether To Stay Core-Only Or Use A Companion

Stay on core only when:
- the repo does not show a confident companion match
- you are exploring a stack that Forge can route but not enrich deeply yet
- you need diagnosis, planning, change artifacts, and release discipline before any stack-specific acceleration

Use a companion when:
- `doctor` or `map-codebase` shows a confident companion match
- the companion exposes a verification pack that fits the repo
- you want faster defaults for known stack conventions and risk checks without changing the core workflow contract

## 3. If A Reference Companion Matches

If the repo matches a reference companion such as `nextjs-typescript-postgres`, Forge may surface:
- companion id
- operator profile
- verification pack

Typical path:
1. `doctor`
2. `map-codebase`
3. start a change artifact for medium or large work
4. use the companion verification pack before claiming completion
5. run `review_pack`
6. run `release_doc_sync`
7. run `release_readiness`

This is an accelerator, not a required path.
If no companion matches confidently, use the same flow with core checks and repo evidence.

## 4. Use Change Artifacts For Medium And Large Work

Run:
- `python packages/forge-core/scripts/change_artifacts.py start --workspace <repo> --summary "<slice>"`

This creates durable work state for:
- proposal
- design
- tasks
- verification

## 5. Use Shipping Intelligence Before Release

Run:
- `python packages/forge-core/scripts/dashboard.py --workspace <repo> --format text`
- `python packages/forge-core/scripts/review_pack.py --workspace <repo> --profile standard --format text`
- `python packages/forge-core/scripts/release_doc_sync.py --workspace <repo> --format text`
- `python packages/forge-core/scripts/release_readiness.py --workspace <repo> --profile auto --format text`

## 6. Use `forge-browse` For Browser QA

For authenticated app flows:
- create a persistent browse session
- create login-aware QA packets
- rerun those packets before release

This is the intended path for product-facing web verification, not one-off screenshots only.

## 7. Do Not Treat Companion Breadth As Product Identity

Forge is process-first.

Current rule:
- harden the universal workflow on real repos first
- keep companions optional and user-chosen
- add or deepen companions only when they strengthen the workflow without becoming the center of product identity
