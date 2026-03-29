import { afterEach, describe, expect, it, vi } from "vitest";

import { healthPayload, observabilityChecklist, observabilityEnvironmentKeys, observabilityReady } from "../lib/observability";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("deploy observability preset", () => {
  it("exposes readiness helpers", () => {
    expect(observabilityEnvironmentKeys()).toContain("SENTRY_DSN");
    expect(observabilityChecklist().length).toBeGreaterThan(0);
  });

  it("reports ready when observability env is present", () => {
    vi.stubEnv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/demo");
    vi.stubEnv("NEXT_PUBLIC_APP_NAME", "Demo App");
    vi.stubEnv("NEXT_PUBLIC_APP_URL", "http://localhost:3000");
    vi.stubEnv("SENTRY_DSN", "https://example.invalid");
    vi.stubEnv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318");
    vi.stubEnv("LOG_LEVEL", "info");

    expect(observabilityReady()).toBe(true);
    expect(healthPayload().ready).toBe(true);
  });
});
