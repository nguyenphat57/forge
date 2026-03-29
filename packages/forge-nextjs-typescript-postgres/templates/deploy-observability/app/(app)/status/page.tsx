import { healthPayload, observabilityChecklist } from "../../../lib/observability";

export default function StatusPage() {
  const health = healthPayload();
  const checklist = observabilityChecklist();
  return (
    <main>
      <h1>Status</h1>
      <p>Deployment readiness view for release confidence.</p>
      <p>Health status: {health.status}</p>
      <ul>
        {checklist.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </main>
  );
}
