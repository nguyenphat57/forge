# Forge Companion Decision Guide

Date: 2026-03-28
Status: current decision guide, aligned to the 2026-03-29 process-first thesis

## Goal

Make it obvious when Forge is operating as:
- core only
- core plus an optional companion

## How To Tell

Check `doctor` or `map-codebase`.

If a companion is active, Forge now reports:
- companion id
- strength
- operator profile
- verification pack

## Choose Core Only When

- the repo does not show a confident companion match
- the stack is unusual or mixed enough that generic orchestration is safer
- you need diagnosis, planning, change artifacts, and verification discipline more than stack-specific scaffolding

## Choose A Companion When

- the repo clearly matches the companion markers
- the companion verification pack matches the work you are doing
- you want faster defaults for commands, risk notes, and review focus without changing core routing or evidence policy

## Current Reference Companion

`nextjs-typescript-postgres` remains a reference companion, not the identity of Forge.

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

The user chooses the stack.
If Forge shows a confident companion match and a verification pack, use it as an accelerator.

If Forge does not show a confident match, stay on the core path and do not force a lane assumption.
