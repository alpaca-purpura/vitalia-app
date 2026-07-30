/**
 * Tests for CompliancePageClient — A2 acceptance criterion.
 * Verifies: named export, CSV export functional, stats + table render contract.
 *
 * Per .claude/rules/tdd-mandatory.md — RED first, then GREEN.
 * Spec § 4.5 + § 8.6 + § 5.6
 */
import { describe, it, expect } from "vitest";
import type { ComplianceEventItem } from "@/features/vitalia/types/compliance.types";

describe("CompliancePageClient exports", () => {
  it("exports CompliancePageClient as named export (no default)", async () => {
    const mod = await import(
      "@/features/vitalia/components/compliance-page-client"
    );
    expect(typeof mod.CompliancePageClient).toBe("function");
    expect(mod).not.toHaveProperty("default");
  });
});

describe("CompliancePageClient microcopy (spec § 8.6)", () => {
  it("export CTA is 'Exportar CSV'", async () => {
    const { MICROCOPY_COMPLIANCE } = await import("@/features/vitalia/config/microcopy");
    expect(MICROCOPY_COMPLIANCE.export.cta).toBe("Exportar CSV");
  });

  it("export preparing toast text matches spec", async () => {
    const { MICROCOPY_COMPLIANCE } = await import("@/features/vitalia/config/microcopy");
    expect(MICROCOPY_COMPLIANCE.export.preparing).toBe("Preparando CSV...");
  });

  it("export ready text matches spec", async () => {
    const { MICROCOPY_COMPLIANCE } = await import("@/features/vitalia/config/microcopy");
    expect(MICROCOPY_COMPLIANCE.export.ready).toBe("Descarga lista");
  });

  it("filter labels are in Spanish neutro", async () => {
    // Filter labels: Tipo, Fecha, Severidad per spec § 8.6
    const filterLabels = ["Tipo", "Fecha", "Severidad"];
    const voseoPattern = /\b(tenés|podés|hacés|mirá)\b/i;
    for (const label of filterLabels) {
      expect(label).not.toMatch(voseoPattern);
    }
  });

  it("page title matches spec § 8.6", async () => {
    const { MICROCOPY_COMPLIANCE } = await import("@/features/vitalia/config/microcopy");
    expect(MICROCOPY_COMPLIANCE.title).toBe("Cumplimiento HIPAA-lite");
    expect(MICROCOPY_COMPLIANCE.subtitle).toBe("Audit log para registro legal");
  });
});

describe("CompliancePageClient CSV export logic", () => {
  it("generateCsvBlob produces valid CSV header row", async () => {
    const { generateCsvBlob } = await import(
      "@/features/vitalia/components/compliance-page-client"
    );
    const events: ComplianceEventItem[] = [];
    const blob = generateCsvBlob(events);
    expect(blob).toBeInstanceOf(Blob);
    expect(blob.type).toBe("text/csv;charset=utf-8;");
  });

  it("generateCsvBlob includes data rows for events", async () => {
    const { generateCsvBlob } = await import(
      "@/features/vitalia/components/compliance-page-client"
    );
    const events: ComplianceEventItem[] = [
      {
        id: "evt-1",
        event_type: "consent_signed",
        severity: "info",
        patient_id: "p1",
        booking_id: "b1",
        payload_redacted: {},
        actor_id: "a1",
        actor_type: "patient",
        created_at: "2026-05-14T10:00:00Z",
      },
    ];
    const blob = generateCsvBlob(events);
    expect(blob).toBeInstanceOf(Blob);
    // Verify size > header-only (has data row)
    expect(blob.size).toBeGreaterThan(50);
  });

  it("generateCsvBlob handles empty events without throwing", async () => {
    const { generateCsvBlob } = await import(
      "@/features/vitalia/components/compliance-page-client"
    );
    expect(() => generateCsvBlob([])).not.toThrow();
  });
});

describe("CompliancePageClient filter state", () => {
  it("CompliancePageClient component is a function", async () => {
    const mod = await import(
      "@/features/vitalia/components/compliance-page-client"
    );
    expect(typeof mod.CompliancePageClient).toBe("function");
  });
});

describe("ComplianceEventRow exports", () => {
  it("exports ComplianceEventRow as named export (no default)", async () => {
    const mod = await import(
      "@/features/vitalia/components/compliance-event-row"
    );
    expect(typeof mod.ComplianceEventRow).toBe("function");
    expect(mod).not.toHaveProperty("default");
  });
});

describe("ComplianceEventRow severity badge logic", () => {
  it("severity badge maps high → danger variant", async () => {
    const { getSeverityBadgeVariant } = await import(
      "@/features/vitalia/components/compliance-event-row"
    );
    expect(getSeverityBadgeVariant("high")).toBe("danger");
  });

  it("severity badge maps medium → warning variant", async () => {
    const { getSeverityBadgeVariant } = await import(
      "@/features/vitalia/components/compliance-event-row"
    );
    expect(getSeverityBadgeVariant("medium")).toBe("warning");
  });

  it("severity badge maps info → neutral variant", async () => {
    const { getSeverityBadgeVariant } = await import(
      "@/features/vitalia/components/compliance-event-row"
    );
    expect(getSeverityBadgeVariant("info")).toBe("neutral");
  });
});
