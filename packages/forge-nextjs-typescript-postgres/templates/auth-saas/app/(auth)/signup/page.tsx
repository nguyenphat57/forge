import { authSecretConfigured } from "../../../lib/auth/session";

export default function SignupPage() {
  return (
    <main>
      <h1>Create account</h1>
      <p>Connect validation, hashing, and persistence in this flow.</p>
      <p>AUTH_SECRET configured: {authSecretConfigured() ? "yes" : "no"}</p>
    </main>
  );
}
