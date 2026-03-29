export function sessionCookieName() {
  return process.env.SESSION_COOKIE_NAME || "forge-session";
}

export function authSecretConfigured() {
  return Boolean(process.env.AUTH_SECRET);
}

export function authEnvironmentKeys() {
  return ["DATABASE_URL", "AUTH_SECRET", "NEXT_PUBLIC_APP_URL", "SESSION_COOKIE_NAME"];
}

export function authReady() {
  return authEnvironmentKeys().every((key) => Boolean(process.env[key]));
}

export function authShipChecklist() {
  return [
    "Document AUTH_SECRET and NEXT_PUBLIC_APP_URL in .env.example.",
    "Keep login, signup, and protected routes behind the shared session cookie.",
    "Re-run auth tests before shipping any session or password change.",
  ];
}
