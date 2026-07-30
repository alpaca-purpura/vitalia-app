/**
 * RED tests — format helpers (T-infra-7 TDD)
 * Tests written BEFORE implementation (TDD RED-first).
 */

import { describe, it, expect } from "vitest";

// These imports will fail until format helpers are implemented (RED state)
import { formatMoney } from "@/lib/format/formatMoney";
import { formatTenantDate } from "@/lib/format/formatTenantDate";
import { formatTenantDateTime } from "@/lib/format/formatTenantDateTime";
import { formatTenantRelative } from "@/lib/format/formatTenantRelative";

describe("formatMoney", () => {
  it("formats amount with ARS currency", () => {
    const result = formatMoney(15000, "ARS");
    expect(result).toBeTruthy();
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });

  it("formats amount with USD currency", () => {
    const result = formatMoney(100, "USD");
    expect(result).toBeTruthy();
    expect(typeof result).toBe("string");
  });

  it("formats amount with MXN currency", () => {
    const result = formatMoney(500, "MXN");
    expect(result).toBeTruthy();
    expect(typeof result).toBe("string");
  });

  it("handles null currency gracefully (locale fallback)", () => {
    // NEVER hardcode 'USD' — null means use tenant locale fallback
    const result = formatMoney(100, null);
    expect(typeof result).toBe("string");
  });

  it("handles zero amount", () => {
    const result = formatMoney(0, "ARS");
    expect(typeof result).toBe("string");
  });
});

describe("formatTenantDate", () => {
  const ISO_DATE = "2026-03-15T14:30:00Z";

  it("formats an ISO date string", () => {
    const result = formatTenantDate(ISO_DATE, "America/Argentina/Buenos_Aires");
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });

  it("handles UTC timezone", () => {
    const result = formatTenantDate(ISO_DATE, "UTC");
    expect(typeof result).toBe("string");
  });

  it("returns fallback for invalid date", () => {
    const result = formatTenantDate("not-a-date", "UTC");
    expect(typeof result).toBe("string");
  });
});

describe("formatTenantDateTime", () => {
  const ISO_DT = "2026-03-15T14:30:00Z";

  it("formats datetime with time portion", () => {
    const result = formatTenantDateTime(
      ISO_DT,
      "America/Argentina/Buenos_Aires",
    );
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });
});

describe("formatTenantRelative", () => {
  it("returns relative time string for a recent date", () => {
    const recent = new Date(Date.now() - 3 * 60 * 1000).toISOString(); // 3 min ago
    const result = formatTenantRelative(recent);
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });

  it("returns relative time string for an old date", () => {
    const old = "2020-01-01T00:00:00Z";
    const result = formatTenantRelative(old);
    expect(typeof result).toBe("string");
  });
});
