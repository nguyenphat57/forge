import { authReady, authShipChecklist, sessionCookieName } from "../lib/auth/session";

export default function HomePage() {
  const checklist = authShipChecklist();
  return (
    <main>
      <h1>__FORGE_PROJECT_NAME__</h1>
      <p>Authentication-ready preset with signup, login, and protected dashboard surfaces.</p>
      <p>Session cookie: {sessionCookieName()}</p>
      <p>Auth ready: {authReady() ? "yes" : "needs env"}</p>
      <ul>
        {checklist.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </main>
  );
}
