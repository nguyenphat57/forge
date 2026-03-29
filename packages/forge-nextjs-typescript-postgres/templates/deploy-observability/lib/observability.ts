export function observabilityEnvironmentKeys() {
  return [
    "DATABASE_URL",
    "NEXT_PUBLIC_APP_NAME",
    "NEXT_PUBLIC_APP_URL",
    "SENTRY_DSN",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "LOG_LEVEL",
  ];
}

export function observabilityChecklist() {
  return [
    "Wire `/api/health` into the deploy probe.",
    "Send release SHA, environment, and request IDs through logs.",
    "Keep SENTRY_DSN and OTEL_EXPORTER_OTLP_ENDPOINT documented in .env.example.",
  ];
}

export function observabilityReady() {
  return observabilityEnvironmentKeys().every((key) => Boolean(process.env[key]));
}

export function healthPayload() {
  const missingEnv = observabilityEnvironmentKeys().filter((key) => !process.env[key]);
  return {
    status: missingEnv.length === 0 ? "ok" : "needs-config",
    ready: missingEnv.length === 0,
    releaseChannel: process.env.NODE_ENV === "production" ? "production" : "preview",
    missingEnv,
  };
}
