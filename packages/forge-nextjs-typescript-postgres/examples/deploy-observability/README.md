# Deploy Observability Example

This is the reference surface for the optional deploy-observability preset.

Use it when:
- the app already has working product flows
- release confidence is the next bottleneck
- health probes, traces, and error visibility need to be explicit

Included surfaces:
- `app/api/health/route.ts`
- `app/(app)/status/page.tsx`
- `lib/observability.ts`
- Prisma `DeploymentSignal` model

Recommended workflow:
1. scaffold the preset
2. wire the env keys in `.env.example`
3. add deploy checks to your platform
4. keep the status page and health route in release verification
