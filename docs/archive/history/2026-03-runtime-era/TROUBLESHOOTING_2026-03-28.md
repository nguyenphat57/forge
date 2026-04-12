# Forge Troubleshooting

Date: 2026-03-28
Status: current troubleshooting, aligned to the 2026-03-29 process-first thesis

## Doctor Warns About Runtime Tools

Meaning:
- core can still work
- optional runtime tools are missing or not registered cleanly

What to do:
- register the runtime tool bundle
- re-run `doctor`

## Doctor Shows A Companion But No Operator Profile

Meaning:
- the repo matches a companion broadly
- the repo is still missing enough markers for a stronger stack-specific command profile

What to do:
- inspect `package.json`
- inspect `.env.example`
- add the expected stack markers for that companion profile
- re-run `doctor` and `map-codebase`

## Map-Codebase Shows The Wrong Verification Pack

Meaning:
- the repo markers still look closer to another feature band

What to do:
- check whether auth, billing, or database markers are incomplete
- confirm which preset shape the repo actually follows

## Release Readiness Fails On Missing Evidence

Meaning:
- Forge is refusing to invent confidence

What to do:
- run `review_pack`
- run `release_doc_sync`
- run a workspace canary
- re-run `release_readiness`

## Browse QA Packets Fail Preflight

Meaning:
- the QA packet declares an authenticated flow but the session state is incomplete

What to do:
- confirm the packet has `auth_required`
- confirm `login_url` is set
- confirm the session has a persisted storage state when the packet requires it

## Companion Expansion Stays Deferred

Meaning:
- Forge is still prioritizing universal workflow quality over more companion breadth

What to do:
- continue hardening the core workflow and brownfield operator surfaces
- use companion demand and evidence only as prioritization input, not as permission to expand early
- do not treat a candidate companion as current policy until the docs and workflow contracts say so
