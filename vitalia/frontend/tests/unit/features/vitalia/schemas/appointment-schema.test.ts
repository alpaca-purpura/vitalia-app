import { describe, it, expect } from "vitest";
import { rescheduleBookingSchema } from "@/features/vitalia/schemas/appointment-schema";

describe("rescheduleBookingSchema", () => {
  it("accepts valid reschedule data", () => {
    const result = rescheduleBookingSchema.safeParse({
      new_slot_iso: "2026-07-10T10:00:00Z",
      reason: "El paciente solicitó otro horario",
    });
    expect(result.success).toBe(true);
  });

  it("accepts reschedule without reason", () => {
    const result = rescheduleBookingSchema.safeParse({
      new_slot_iso: "2026-07-10T10:00:00Z",
    });
    expect(result.success).toBe(true);
  });

  it("rejects missing new_slot_iso", () => {
    const result = rescheduleBookingSchema.safeParse({
      reason: "Conflicto de agenda",
    });
    expect(result.success).toBe(false);
  });

  it("rejects reason longer than 500 chars", () => {
    const result = rescheduleBookingSchema.safeParse({
      new_slot_iso: "2026-07-10T10:00:00Z",
      reason: "a".repeat(501),
    });
    expect(result.success).toBe(false);
  });
});
