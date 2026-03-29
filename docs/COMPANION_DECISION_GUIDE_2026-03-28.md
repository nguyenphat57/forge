# Forge Companion Decision Guide

Date: 2026-03-28

## Goal

Make it obvious when Forge is operating as:
- core only
- core plus a first-party companion

## How To Tell

Check `doctor` or `map-codebase`.

If a companion is active, Forge now reports:
- companion id
- strength
- operator profile
- verification pack

## Choose Core Only When

- the repo does not match a first-party companion
- the stack is unusual or mixed enough that generic orchestration is safer
- you need diagnosis, planning, change artifacts, and verification discipline more than stack-specific scaffolding

## Choose A Companion When

- the repo clearly matches the companion markers
- the companion verification pack matches the work you are doing
- you want faster defaults for commands, risk notes, and review focus

## Current First-Party Companion

`nextjs-typescript-postgres`

Use it when the repo shows signals such as:
- `next`
- `tsconfig.json`
- Prisma or another Postgres adapter
- App Router markers

Feature-aware depth currently includes:
- baseline web app
- auth-oriented app
- billing-oriented app
- deploy and observability guidance

## What A Companion Must Not Change

A companion can enrich:
- `doctor`
- `map-codebase`
- init presets
- command profiles
- verification packs
- review focus

A companion must not replace:
- routing
- evidence policy
- quality gate decisions
- release verdict logic

## Practical Rule

If Forge shows a companion match and a verification pack, use it.

If Forge does not show a confident match, stay on the core path and do not force a lane assumption.
