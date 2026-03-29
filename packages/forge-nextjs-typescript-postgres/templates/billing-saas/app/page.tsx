import { billingShipChecklist, stripeWebhookConfigured } from "../lib/billing/stripe";

export default function HomePage() {
  const checklist = billingShipChecklist();
  return (
    <main>
      <h1>__FORGE_PROJECT_NAME__</h1>
      <p>Billing-ready preset with Stripe, auth, and subscription placeholders.</p>
      <p>Webhook configured: {stripeWebhookConfigured() ? "yes" : "needs env"}</p>
      <ul>
        {checklist.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </main>
  );
}
