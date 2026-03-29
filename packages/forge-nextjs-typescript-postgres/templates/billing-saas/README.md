# __FORGE_PROJECT_NAME__

Forge billing preset for a Next.js + TypeScript + Postgres product.

Included baseline:
- auth-ready entry surfaces
- billing page and Stripe webhook route
- subscription-oriented Prisma schema placeholders

Product-ready notes:
- document `AUTH_SECRET`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and `STRIPE_PRICE_ID`
- keep the shared session cookie contract explicit
- treat the webhook route as a required release gate
- rerun `test:billing` before shipping billing or entitlement changes
