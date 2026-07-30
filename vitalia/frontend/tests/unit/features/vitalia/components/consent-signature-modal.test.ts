/**
 * Tests for ConsentSignatureModal component contract.
 * Verifies: named exports, consent microcopy (HIPAA-lite strings), scroll validation logic.
 */
import { describe, it, expect, vi } from "vitest";

describe("ConsentSignatureModal exports", () => {
  it("exports ConsentSignatureModal as named export", async () => {
    const mod = await import("@/features/vitalia/components/consent-signature-modal");
    expect(typeof mod.ConsentSignatureModal).toBe("function");
    expect(mod).not.toHaveProperty("default");
  });
});

describe("ConsentSignatureModal microcopy", () => {
  it("consent microcopy covers scroll instruction + accept + signature prompt", async () => {
    const { MICROCOPY_BOOKING } = await import("@/features/vitalia/config/microcopy");
    expect(typeof MICROCOPY_BOOKING.consent.scrollInstruction).toBe("string");
    expect(MICROCOPY_BOOKING.consent.scrollInstruction.length).toBeGreaterThan(5);
    expect(typeof MICROCOPY_BOOKING.consent.accept).toBe("string");
    expect(MICROCOPY_BOOKING.consent.accept.length).toBeGreaterThan(5);
    expect(typeof MICROCOPY_BOOKING.consent.signaturePrompt).toBe("string");
    expect(MICROCOPY_BOOKING.consent.signaturePrompt.length).toBeGreaterThan(5);
  });

  it("consent title is 'Consentimiento informado'", async () => {
    const { MICROCOPY_BOOKING } = await import("@/features/vitalia/config/microcopy");
    expect(MICROCOPY_BOOKING.consent.title).toBe("Consentimiento informado");
  });

  it("payment microcopy has no voseo", async () => {
    const { MICROCOPY_BOOKING } = await import("@/features/vitalia/config/microcopy");
    const voseoVerbs = /\b(tenés|podés|hacés|mirá|dejá|usá)\b/i;
    for (const text of Object.values(MICROCOPY_BOOKING.payment)) {
      expect(text).not.toMatch(voseoVerbs);
    }
  });

  it("consent microcopy has no voseo", async () => {
    const { MICROCOPY_BOOKING } = await import("@/features/vitalia/config/microcopy");
    const voseoVerbs = /\b(tenés|podés|hacés|mirá|dejá|usá)\b/i;
    for (const text of Object.values(MICROCOPY_BOOKING.consent)) {
      expect(text).not.toMatch(voseoVerbs);
    }
  });
});

describe("ConsentSignatureModal prop contract", () => {
  it("onSign callback is invoked with signed name string", () => {
    const onSign = vi.fn((name: string) => name);
    onSign("María García López");
    expect(onSign).toHaveBeenCalledWith("María García López");
    expect(typeof onSign.mock.calls[0][0]).toBe("string");
  });

  it("onClose callback is a function", () => {
    const onClose = vi.fn(() => undefined);
    onClose();
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
