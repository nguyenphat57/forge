# Contributing To Forge

## Scope

Use this repo to change source packages, overlays, runtime tools, tests, and docs.
Do not edit installed runtimes or generated `dist/` bundles by hand.

## Development Flow

1. Make changes in `packages/`, `scripts/`, `tests/`, or `docs/`.
2. Regenerate any host artifacts if a canonical source changed.
3. Run `python scripts/verify_repo.py`.
4. Update docs when behavior, rollout guidance, or operator flow changes.

## Repo Rules

- Keep `packages/forge-core` host-agnostic.
- Put host-specific behavior in the matching adapter package.
- Treat runtime tools such as `forge-browse` and `forge-design` as separate bundles.
- Keep public docs in English unless the file is explicitly maintainer-facing operational context.

## Generated Artifacts

- `dist/` is a release artifact, not a source directory.
- Generated host files must come from their canonical source inputs.
- If `scripts/generate_host_artifacts.py --check` fails, regenerate before submitting changes.

## Verification

The canonical repo gate is:

```powershell
python scripts/verify_repo.py
```

If you changed a narrower surface, run the most relevant local verification first, then the full repo gate before closing the change.

## Pull Requests

Include:

- what changed
- why the change was needed
- what verification was run
- any remaining risk or follow-up

## Issues

Use issues for bugs, docs gaps, release blockers, and feature proposals.
For security-sensitive reports, follow [SECURITY.md](SECURITY.md).
