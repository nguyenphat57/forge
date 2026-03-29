import { NextResponse } from "next/server";
import { stripeWebhookConfigured } from "../../../../lib/billing/stripe";

export async function POST(request: Request) {
  return NextResponse.json({
    status: stripeWebhookConfigured() ? "accepted" : "needs-config",
    configured: stripeWebhookConfigured(),
    signatureReceived: Boolean(request.headers.get("stripe-signature")),
  });
}
