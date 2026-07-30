import { describe, it, expect } from "vitest";
import { bookingCreateSchema } from "@/features/vitalia/schemas/booking-schema";

describe("bookingCreateSchema", () => {
  const validBooking = {
    offer_id: "550e8400-e29b-41d4-a716-446655440001",
    doctor_id: "550e8400-e29b-41d4-a716-446655440002",
    patient_id: "550e8400-e29b-41d4-a716-446655440003",
    slot_iso: "2026-06-15T14:00:00Z",
    delivery_channel: "whatsapp" as const,
  };

  it("accepts valid booking creation data", () => {
    const result = bookingCreateSchema.safeParse(validBooking);
    expect(result.success).toBe(true);
  });

  it("rejects invalid delivery_channel", () => {
    const result = bookingCreateSchema.safeParse({
      ...validBooking,
      delivery_channel: "sms",
    });
    expect(result.success).toBe(false);
  });

  it("rejects missing offer_id", () => {
    const { offer_id: _omit, ...rest } = validBooking;
    const result = bookingCreateSchema.safeParse(rest);
    expect(result.success).toBe(false);
  });

  it("accepts all valid delivery_channel values", () => {
    const channels = ["whatsapp", "email", "both"] as const;
    for (const delivery_channel of channels) {
      const result = bookingCreateSchema.safeParse({ ...validBooking, delivery_channel });
      expect(result.success).toBe(true);
    }
  });

  it("accepts optional consent fields", () => {
    const result = bookingCreateSchema.safeParse({
      ...validBooking,
      consent_template_slug: "dental_implant_v1",
      requires_informed_consent: true,
      requires_prepay: true,
      deposit_only: false,
    });
    expect(result.success).toBe(true);
  });
});
