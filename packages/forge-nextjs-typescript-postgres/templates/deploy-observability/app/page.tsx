import { healthPayload, observabilityChecklist } from "../lib/observability";

export default function HomePage() {
  const checklist = observabilityChecklist();
  const health = healthPayload();
  return (
    <main>
      <h1>__FORGE_PROJECT_NAME__</h1>
      <p>Deploy-observability preset with health, traces, and release visibility.</p>
      <p>Health status: {health.status}</p>
      <p>Missing env: {health.missingEnv.length > 0 ? health.missingEnv.join(", ") : "none"}</p>
      <ul>
        {checklist.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </main>
  );
}
