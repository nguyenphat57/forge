import { authReady, authShipChecklist } from "../../../lib/auth/session";

export default function DashboardPage() {
  const checklist = authShipChecklist();
  return (
    <main>
      <h1>Dashboard</h1>
      <p>Protected product surface for authenticated users.</p>
      <p>Auth ready: {authReady() ? "yes" : "needs env"}</p>
      <ul>
        {checklist.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </main>
  );
}
