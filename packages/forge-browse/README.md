# Forge Browse

`forge-browse` is the first Forge runtime tool bundle.

## Goal

Provide a browser-side actuator without pushing browser automation into `forge-core`.

`forge_browse.py` is the canonical operator entrypoint.

`browse_server.py` is an optional local HTTP control plane for deterministic smoke checks and installed-bundle assertions.

## MVP

- one shared persistent state contract across CLI, server, build manifests, and installed bundles
- deterministic `open` / `snapshot` / `assert-text` through the local HTTP control plane
- persistent logical sessions backed by bundle state
- optional Playwright CLI health check
- optional Playwright-backed screenshot capture with persisted storage state
- optional Playwright-backed PDF export with persisted storage state
- optional interactive `open` and `record` entry points using the same session data

## Failure Model

- If `node` or `npx playwright` is unavailable, Playwright-backed commands return a structured failure.
- If Playwright browser binaries are missing, the Playwright path fails and preserves the session state for retry.
- The HTTP control plane does not require Playwright and remains available for deterministic repo-level smoke checks.
- The bundle builds and verifies without requiring a live browser run.

## Live Smoke

To exercise the real Playwright path during bundle verify:

```powershell
npx playwright install chromium
$env:FORGE_BROWSE_RUN_PLAYWRIGHT_SMOKE = "1"
python scripts/verify_bundle.py --format json
```

The live smoke drives the canonical CLI surface through `session-create`, `snapshot`, and `session-show` on a local temporary site.

## Live Verification

- Set `FORGE_BROWSE_RUN_PLAYWRIGHT_SMOKE=1` before `python scripts/verify_bundle.py --format json` to enable a real local Playwright screenshot smoke.
- The live smoke uses a temporary local page, a temporary bundle state root, and the canonical `playwright_cli` execution path.
