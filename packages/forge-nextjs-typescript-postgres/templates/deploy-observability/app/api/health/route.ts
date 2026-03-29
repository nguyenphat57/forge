import { NextResponse } from "next/server";
import { healthPayload } from "../../../lib/observability";

export async function GET() {
  return NextResponse.json(healthPayload());
}
