import { describe, it, expect } from "vitest";
import { manualHandoffSchema } from "@/features/vitalia/schemas/handoff-schema";

describe("manualHandoffSchema", () => {
  it("accepts empty object (reason optional)", () => {
    const result = manualHandoffSchema.safeParse({});
    expect(result.success).toBe(true);
  });

  it("accepts reason string", () => {
    const result = manualHandoffSchema.safeParse({
      reason: "El paciente tiene dudas sobre el tratamiento",
    });
    expect(result.success).toBe(true);
  });

  it("accepts null reason", () => {
    const result = manualHandoffSchema.safeParse({ reason: null });
    expect(result.success).toBe(true);
  });

  it("rejects reason longer than 500 chars", () => {
    const result = manualHandoffSchema.safeParse({
      reason: "a".repeat(501),
    });
    expect(result.success).toBe(false);
  });
});
