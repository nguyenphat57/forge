# Forge Nextjs Typescript Postgres

First-party Forge companion for the `nextjs + typescript + postgres` product path.

This package is not an orchestrator. `forge-core` stays responsible for routing,
verification policy, change-artifact gates, and reporting. This companion only
supplies stack-specific presets, commands, doctor checks, map enrichers, and
verification data.

Current first-party presets:
- baseline SaaS
- auth SaaS
- billing SaaS
- deploy observability
