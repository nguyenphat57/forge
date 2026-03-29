import { authReady, sessionCookieName } from "../../../lib/auth/session";

export default function LoginPage() {
  return (
    <main>
      <h1>Log in</h1>
      <p>Wire credentials, session handling, and billing-gated access here.</p>
      <p>Session cookie: {sessionCookieName()}</p>
      <p>Auth ready: {authReady() ? "yes" : "needs env"}</p>
    </main>
  );
}
