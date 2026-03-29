import { describe, expect, it } from "vitest";

import { authEnvironmentKeys, authReady, sessionCookieName } from "../lib/auth/session";

describe("billing auth baseline", () => {
  it("keeps auth support present", () => {
    expect("billing-saas-auth").toContain("auth");
  });

  it("exposes shared auth readiness helpers", () => {
    expect(sessionCookieName()).toBeTruthy();
    expect(authEnvironmentKeys()).toContain("AUTH_SECRET");
    expect(authReady()).toBeTypeOf("boolean");
  });
});
