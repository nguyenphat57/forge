export function sessionCookieName() {
  return process.env.SESSION_COOKIE_NAME || "forge-session";
}

export function authEnvironmentKeys() {
  return ["DATABASE_URL", "AUTH_SECRET", "SESSION_COOKIE_NAME", "NEXT_PUBLIC_APP_URL"];
}

export function authReady() {
  return authEnvironmentKeys().every((key) => Boolean(process.env[key]));
}
