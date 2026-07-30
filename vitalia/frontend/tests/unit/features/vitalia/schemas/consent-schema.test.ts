import { describe, it, expect } from "vitest";
import { consentSignSchema } from "@/features/vitalia/schemas/consent-schema";

describe("consentSignSchema", () => {
  it("accepts valid consent sign typed_name", () => {
    const result = consentSignSchema.safeParse({
      signed_name: "Juan Perez",
      signature_method: "typed_name",
      consent_token: "eyJhbGciOiJIUzI1NiJ9.payload.signature",
    });
    expect(result.success).toBe(true);
  });

  it("accepts signature_pad method", () => {
    const result = consentSignSchema.safeParse({
      signed_name: "María García",
      signature_method: "signature_pad",
      consent_token: "eyJhbGciOiJIUzI1NiJ9.payload.signature",
    });
    expect(result.success).toBe(true);
  });

  it("rejects empty signed_name", () => {
    const result = consentSignSchema.safeParse({
      signed_name: "J",
      signature_method: "typed_name",
      consent_token: "token",
    });
    expect(result.success).toBe(false);
  });

  it("rejects invalid signature_method", () => {
    const result = consentSignSchema.safeParse({
      signed_name: "Juan Perez",
      signature_method: "biometric",
      consent_token: "token",
    });
    expect(result.success).toBe(false);
  });

  it("rejects missing consent_token", () => {
    const result = consentSignSchema.safeParse({
      signed_name: "Juan Perez",
      signature_method: "typed_name",
    });
    expect(result.success).toBe(false);
  });
});
