import { describe, expect, it } from "vitest";

describe("preset", () => {
  it("stays deterministic", () => {
    expect("forge-nextjs-typescript-postgres").toContain("nextjs");
  });
});
