import { billingShipChecklist } from "../../../lib/billing/stripe";

export default function BillingPage() {
  const checklist = billingShipChecklist();
  return (
    <main>
      <h1>Billing</h1>
      <p>Connect customer portal, plans, webhook handling, and subscription state here.</p>
      <ul>
        {checklist.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </main>
  );
}
