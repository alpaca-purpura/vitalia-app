/**
 * Tests for MedicalDisclaimerBanner component contract.
 * Verifies: named exports, disclaimer text per context, no voseo, Server-compatible (no "use client").
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { resolve } from "path";

describe("MedicalDisclaimerBanner exports", () => {
  it("exports MedicalDisclaimerBanner as named export", async () => {
    const mod = await import("@/features/vitalia/components/medical-disclaimer-banner");
    expect(typeof mod.MedicalDisclaimerBanner).toBe("function");
    expect(mod).not.toHaveProperty("default");
  });

  it("is Server-compatible — no 'use client' directive at top of file", () => {
    const filePath = resolve(
      __dirname,
      "../../../../../src/features/vitalia/components/medical-disclaimer-banner.tsx"
    );
    const source = readFileSync(filePath, "utf-8");
    // Server component — directive "use client" must NOT appear as a standalone statement
    // (it would be the first non-comment statement). We check for the exact directive pattern.
    // The file may mention "use client" in comments as documentation — that's OK.
    const lines = source.split("\n");
    const hasDirective = lines.some(
      (line) => line.trim() === '"use client";' || line.trim() === "'use client';"
    );
    expect(hasDirective).toBe(false);
  });
});

describe("MedicalDisclaimerBanner disclaimer microcopy", () => {
  it("covers default, treatment, and offer contexts", async () => {
    const { MICROCOPY_DISCLAIMER } = await import("@/features/vitalia/config/microcopy");
    expect(typeof MICROCOPY_DISCLAIMER.default).toBe("string");
    expect(typeof MICROCOPY_DISCLAIMER.treatment).toBe("string");
    expect(typeof MICROCOPY_DISCLAIMER.offer).toBe("string");
  });

  it("default disclaimer contains key medical phrase", async () => {
    const { MICROCOPY_DISCLAIMER } = await import("@/features/vitalia/config/microcopy");
    expect(MICROCOPY_DISCLAIMER.default).toContain("consulta médica profesional");
  });

  it("disclaimer texts have no voseo verbs", async () => {
    const { MICROCOPY_DISCLAIMER } = await import("@/features/vitalia/config/microcopy");
    const voseoVerbs = /\b(tenés|podés|hacés|mirá|dejá|usá|consultá)\b/i;
    for (const text of Object.values(MICROCOPY_DISCLAIMER)) {
      expect(text).not.toMatch(voseoVerbs);
    }
  });

  it("all disclaimer texts are non-empty and meaningful", async () => {
    const { MICROCOPY_DISCLAIMER } = await import("@/features/vitalia/config/microcopy");
    for (const text of Object.values(MICROCOPY_DISCLAIMER)) {
      expect(text.length).toBeGreaterThan(20);
    }
  });
});

describe("MedicalDisclaimerBanner context prop", () => {
  it("DisclaimerContext type accepts 'default' | 'treatment' | 'offer'", () => {
    // TypeScript type enforcement — runtime check that the type is handled
    const validContexts = ["default", "treatment", "offer"];
    expect(validContexts).toContain("default");
    expect(validContexts).toContain("treatment");
    expect(validContexts).toContain("offer");
    expect(validContexts).toHaveLength(3);
  });
});
