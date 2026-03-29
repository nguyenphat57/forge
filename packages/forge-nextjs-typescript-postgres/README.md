# Forge Nextjs Typescript Postgres

Source-only example companion for the `nextjs + typescript + postgres` stack path.

This package is a reference companion, not Forge identity. `forge-core` still
owns routing, verification policy, change-artifact gates, and reporting.

This companion only supplies stack-specific presets, commands, doctor checks,
map enrichers, and verification data when the repo clearly wants that stack.
It is not part of the shipped `dist/` bundle matrix and does not track the
monorepo release version.

Reference presets:
- baseline SaaS
- auth SaaS
- billing SaaS
- deploy observability
