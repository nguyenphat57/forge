import { authEnvironmentKeys, sessionCookieName } from "../../../lib/auth/session";

export default function LoginPage() {
  const envKeys = authEnvironmentKeys();
  return (
    <main>
      <h1>Log in</h1>
      <p>Wire credentials, hashing, and session handling here.</p>
      <p>Session cookie: {sessionCookieName()}</p>
      <p>Required env: {envKeys.join(", ")}</p>
    </main>
  );
}
