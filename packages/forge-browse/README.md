# Forge Browse

`forge-browse` is an optional stack-agnostic Forge runtime tool for browser QA.

## Goal

Provide a reusable browser-side actuator without pushing browser automation into `forge-core`.

This tool should stay useful whether the repo is running on the core-only path or with an optional companion active.
It is not tied to one framework or one companion.

`forge_browse.py` is the canonical operator entrypoint.

`browse_server.py` is an optional local HTTP control plane for deterministic smoke checks and installed-bundle assertions.

## Boundary

- `forge-core` owns routing, verification policy, release verdicts, and durable work state.
- `forge-browse` owns browser execution, persisted sessions, QA packets, and capture artifacts.
- `forge-design` can produce review packets, but `forge-browse` stays the runtime QA executor.

## MVP

- one shared persistent state contract across CLI, server, build manifests, and installed bundles
- deterministic `open` / `snapshot` / `assert-text` through the local HTTP control plane
- persistent logical sessions backed by bundle state
- reusable QA packets for repeatable smoke and screenshot flows on top of persistent sessions
- login-aware QA packets with preflight checks and runtime storage-state reuse for authenticated flows
- optional Playwright CLI health check
- optional Playwright-backed screenshot capture with persisted storage state
- optional Playwright-backed PDF export with persisted storage state
- optional interactive `open` and `record` entry points using the same session data

Example authenticated packet:

```powershell
python scripts/forge_browse.py qa-create --session <session-id> --name auth-smoke --url https://example.test/app --auth-required --login-url https://example.test/login --expect-text "Welcome back"
```

Authenticated packets fail fast when the session does not have the required storage state file or the packet omits a login URL. When the storage state contains matching cookies for the target URL, the runtime reuses those cookies during the HTML smoke itself instead of treating auth as preflight-only metadata.

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
