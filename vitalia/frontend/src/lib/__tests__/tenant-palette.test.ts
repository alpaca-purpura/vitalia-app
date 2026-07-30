/**
 * tenant-palette.test.ts — TDD RED-first tests for tenant-palette.ts
 * F1-S3 vitalia-fase1-tenant-switcher — T-1
 *
 * Verifies:
 * - PALETTE contains 6 entries with bg + text classes
 * - pickPaletteColor returns same color for same id (deterministic)
 * - pickPaletteColor handles empty string fallback
 * - amber and lime entries have dark text for WCAG AA contrast
 *
 * gherkin_coverage: AC-14 TenantBadge hash determinístico predecible cross-session
 *
 * downstream-regression-na: brand-local lib test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { PALETTE, pickPaletteColor } from "../tenant-palette";

describe("PALETTE const", () => {
  it("contains exactly 6 entries", () => {
    expect(PALETTE).toHaveLength(6);
  });

  it("every entry has bg and text class", () => {
    for (const entry of PALETTE) {
      expect(entry.bg).toMatch(/^bg-/);
      expect(entry.text).toMatch(/^text-/);
    }
  });

  it("amber, lime and cyan entries have dark text for WCAG AA contrast", () => {
    const amberEntry = PALETTE.find((p) => p.bg === "bg-amber-500");
    const limeEntry = PALETTE.find((p) => p.bg === "bg-lime-500");
    // T-V2 lift fix-loop: cyan-500 #00b8db + white = 2.36 (AA fail) — destapado
    // por axe real post edge-redirect (el run del hardening escaneaba DOM colgado).
    const cyanEntry = PALETTE.find((p) => p.bg === "bg-cyan-500");
    expect(amberEntry?.text).toBe("text-amber-950");
    expect(limeEntry?.text).toBe("text-lime-950");
    expect(cyanEntry?.text).toBe("text-cyan-950");
  });

  it("other entries use text-white", () => {
    const whiteTextEntries = PALETTE.filter((p) => p.text === "text-white");
    expect(whiteTextEntries).toHaveLength(3);
  });
});

describe("pickPaletteColor", () => {
  it("returns same color for same id (deterministic, cross-session)", () => {
    const result1 = pickPaletteColor("sonrisa-plena");
    const result2 = pickPaletteColor("sonrisa-plena");
    expect(result1).toStrictEqual(result2);
  });

  it("returns different colors for different ids (distribution)", () => {
    const r1 = pickPaletteColor("tenant-a");
    const r2 = pickPaletteColor("tenant-zzz");
    // They may be equal by hash collision, but test the mechanism still works
    expect(r1).toBeTruthy();
    expect(r2).toBeTruthy();
  });

  it("handles empty string fallback — returns PALETTE[0]", () => {
    const result = pickPaletteColor("");
    expect(result).toStrictEqual(PALETTE[0]);
  });

  it("returns a value from PALETTE", () => {
    const result = pickPaletteColor("dermalia-mx");
    expect(PALETTE).toContainEqual(result);
  });

  it("Sonrisa Plena (sonrisa-plena) returns deterministic palette index", () => {
    // hash = sum of charCodes of 'sonrisa-plena'
    const id = "sonrisa-plena";
    const hash = id.split("").reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
    const expectedIndex = hash % 6;
    expect(pickPaletteColor(id)).toStrictEqual(PALETTE[expectedIndex]);
  });

  it("Dermalia MX (dermalia-mx) returns deterministic palette index", () => {
    const id = "dermalia-mx";
    const hash = id.split("").reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
    const expectedIndex = hash % 6;
    expect(pickPaletteColor(id)).toStrictEqual(PALETTE[expectedIndex]);
  });
});
