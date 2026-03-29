---
name: forge-nextjs-typescript-postgres
description: "Optional reference companion for Next.js + TypeScript + Postgres repos and presets."
---

# Forge Nextjs Typescript Postgres

Use this companion when:
- the user explicitly asks for Next.js
- the repo clearly contains `next`
- the repo or workspace was scaffolded from this companion preset

Do not use this companion when:
- the repo is only generic Node.js without Next.js
- the project is Electron-first, mobile-first, or shell-first
- the stack is ambiguous and `forge-core` has not established the runtime yet

This companion is an optional adaptation layer. It should reinforce the stack
the repo already chose, not define Forge identity for unrelated work.

Runtime context to confirm quickly:
- Stack/framework: Next.js App Router + TypeScript + Postgres-oriented data layer
- Primary commands: `dev`, `build`, `lint`, `typecheck`, `test`, schema commands
- Conventions to keep: app router boundaries, typed server-side data access, env and schema hygiene
- Stack-specific risks: migration drift, auth/session regressions, env misconfiguration, cache and build assumptions
