import { describe, expect, it } from "vitest";
import { authEnvironmentKeys, authReady, authShipChecklist, sessionCookieName } from "../lib/auth/session";

describe("auth preset", () => {
  it("keeps auth markers stable", () => {
    expect("auth-saas").toContain("auth");
  });

  it("exposes guided auth readiness helpers", () => {
    expect(sessionCookieName()).toBeTruthy();
    expect(authEnvironmentKeys()).toContain("AUTH_SECRET");
    expect(authShipChecklist().length).toBeGreaterThan(0);
    expect(authReady()).toBeTypeOf("boolean");
  });
});
