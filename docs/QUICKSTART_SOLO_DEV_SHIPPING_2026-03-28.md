# Forge Solo-Dev Shipping Quickstart

Date: 2026-03-28
Audience: one solo developer who wants a dependable path from repo onboarding to release checks

## 1. Start With Core Diagnosis

Run:
- `python packages/forge-core/scripts/doctor.py --workspace <repo> --format text`
- `python packages/forge-core/scripts/map_codebase.py --workspace <repo> --format text`

What this gives you:
- environment and runtime health
- matched companion summary
- active operator profile and verification pack when a first-party companion applies
- a durable brownfield map under `.forge-artifacts/codebase/`

## 2. Decide Whether To Stay Core-Only Or Use A Companion

Stay on core only when:
- the repo does not match a first-party companion
- you are exploring a stack that Forge can route but not optimize deeply yet

Use a companion when:
- `doctor` or `map-codebase` shows a matched companion
- the companion exposes a verification pack that fits the repo
- you want a faster path for known stack conventions and risk checks

## 3. For Next.js + TypeScript + Postgres

If the repo matches `nextjs-typescript-postgres`, Forge will surface:
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

## 7. Do Not Open Lane 2 Prematurely

Forge is intentionally shallow in first-party breadth.

Current rule:
- harden lane 1 on real repos first
- only then score and gate a second lane such as Electron or Vite + Capacitor + Supabase
