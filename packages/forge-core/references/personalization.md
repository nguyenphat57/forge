# Forge Personalization

> Muc tieu: giu response-style preferences o `forge-core` theo kieu host-neutral de moi adapter chi can them wrapper UX, khong fork logic.

## Core Contract

- Schema canonical nam tai `data/preferences-schema.json`
- Resolver canonical nam tai `scripts/resolve_preferences.py`
- Workspace-local file mac dinh: `.brain/preferences.json`
- Adapter co the them flow `customize`, nhung khong duoc doi key names hay meaning cua schema

## Supported Fields

| Field | Values | Default | Muc dich |
|------|--------|---------|---------|
| `technical_level` | `newbie`, `basic`, `technical` | `basic` | Dieu chinh muc do giai thich thuat ngu |
| `detail_level` | `concise`, `balanced`, `detailed` | `balanced` | Dieu chinh do sau va do dai response |
| `autonomy_level` | `guided`, `balanced`, `autonomous` | `balanced` | Dieu chinh muc do chu dong khi day task di tiep |
| `personality` | `default`, `mentor`, `strict-coach` | `default` | Dieu chinh tone coaching |

## Resolution Order

1. Neu co `--preferences-file`, dung file do va fail neu file khong ton tai.
2. Neu co `--workspace`, doc `.brain/preferences.json` trong workspace do.
3. Neu khong co file hop le, dung defaults tu schema.

## Validation Rules

- Invalid JSON hoac value sai enum se fallback ve default trong non-strict mode va tra warning.
- `--strict` bien warning thanh hard failure.
- Alias nhu `strict_coach`, `beginner`, `verbose`, `low`, `high` duoc normalize ve enum canonical.

## Response Style Resolver

Resolver khong tao host-specific command surface. No chi tra ve response-style contract de adapter hoac prompt entrypoint co the ap dung:

- terminology policy
- explanation policy
- verbosity/context depth
- decision/autonomy policy
- tone/teaching/challenge style

## Adapter Boundary

- `forge-antigravity`: co the them `/customize` hoac onboarding thin wrapper tren schema nay.
- `forge-codex`: nen giu natural-language customize flow, khong slash-heavy by default.
- `forge-claude` trong tuong lai phai co the tai su dung schema nay gan nhu nguyen ven.
