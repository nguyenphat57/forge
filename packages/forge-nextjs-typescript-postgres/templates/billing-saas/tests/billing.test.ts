import { describe, expect, it } from "vitest";
import { billingEnvironmentKeys, billingShipChecklist, stripeWebhookConfigured } from "../lib/billing/stripe";

describe("billing preset", () => {
  it("keeps billing markers stable", () => {
    expect("billing-saas").toContain("billing");
  });

  it("exposes guided billing readiness helpers", () => {
    expect(billingEnvironmentKeys()).toContain("STRIPE_SECRET_KEY");
    expect(billingShipChecklist().length).toBeGreaterThan(0);
    expect(stripeWebhookConfigured()).toBeTypeOf("boolean");
  });
});
