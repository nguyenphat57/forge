import Stripe from "stripe";

export function stripeClient() {
  return new Stripe(process.env.STRIPE_SECRET_KEY || "sk_test_placeholder");
}

export function stripeWebhookConfigured() {
  return Boolean(process.env.STRIPE_SECRET_KEY) && Boolean(process.env.STRIPE_WEBHOOK_SECRET);
}

export function billingEnvironmentKeys() {
  return ["DATABASE_URL", "AUTH_SECRET", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_ID", "NEXT_PUBLIC_APP_URL"];
}

export function billingShipChecklist() {
  return [
    "Document STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, and STRIPE_PRICE_ID in .env.example.",
    "Keep billing UI, webhook handling, and subscription state aligned.",
    "Re-run billing tests before release when entitlement logic changes.",
  ];
}
