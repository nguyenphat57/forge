# __FORGE_PROJECT_NAME__

Forge auth preset for a Next.js + TypeScript + Postgres product.

Included baseline:
- signup and login screens
- password helpers
- Prisma-backed user and session schema

Product-ready notes:
- document `AUTH_SECRET`, `NEXT_PUBLIC_APP_URL`, and `SESSION_COOKIE_NAME`
- keep protected routes behind a session check
- rerun `test:auth` before release if auth or session logic changes
