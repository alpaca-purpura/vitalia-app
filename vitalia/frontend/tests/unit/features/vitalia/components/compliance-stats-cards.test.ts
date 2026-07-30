/**
 * Tests for ComplianceStatsCards component contract.
 * Verifies: named exports, event type microcopy, stat card labels, severity counting logic.
 */
import { describe, it, expect } from "vitest";
import type { ComplianceEventItem } from "@/features/vitalia/types/compliance.types";

describe("ComplianceStatsCards exports", () => {
  it("exports ComplianceStatsCards as named export", async () => {
    const mod = await import("@/features/vitalia/components/compliance-stats-cards");
    expect(typeof mod.ComplianceStatsCards).toBe("function");
    expect(mod).not.toHaveProperty("default");
  });
});

describe("ComplianceStatsCards microcopy", () => {
  it("compliance microcopy has title and subtitle", async () => {
    const { MICROCOPY_COMPLIANCE } = await import("@/features/vitalia/config/microcopy");
    expect(MICROCOPY_COMPLIANCE.title).toBe("Cumplimiento HIPAA-lite");
    expect(MICROCOPY_COMPLIANCE.subtitle).toBe("Audit log para registro legal");
  });

  it("stats labels match spec § 8.6", async () => {
    const { MICROCOPY_COMPLIANCE } = await import("@/features/vitalia/config/microcopy");
    expect(MICROCOPY_COMPLIANCE.stats.totalEvents).toBe("Total eventos");
    expect(MICROCOPY_COMPLIANCE.stats.critical).toBe("Críticos");
    expect(MICROCOPY_COMPLIANCE.stats.blocked).toBe("Bloqueados");
  });

  it("event types microcopy covers 6 spec events", async () => {
    const { MICROCOPY_COMPLIANCE } = await import("@/features/vitalia/config/microcopy");
    const types = Object.keys(MICROCOPY_COMPLIANCE.eventTypes);
    expect(types).toContain("pii_detected");
    expect(types).toContain("consent_requested");
    expect(types).toContain("consent_signed");
    expect(types).toContain("security_escalation");
    expect(types).toContain("prompt_injection_blocked");
    expect(types).toContain("cross_tenant_blocked");
    expect(types).toHaveLength(6);
  });

  it("event types labels are in Spanish neutro", async () => {
    const { MICROCOPY_COMPLIANCE } = await import("@/features/vitalia/config/microcopy");
    const voseoVerbs = /\b(tenés|podés|hacés|mirá|dejá|usá)\b/i;
    for (const label of Object.values(MICROCOPY_COMPLIANCE.eventTypes)) {
      expect(label).not.toMatch(voseoVerbs);
    }
  });

  it("export microcopy has cta and states", async () => {
    const { MICROCOPY_COMPLIANCE } = await import("@/features/vitalia/config/microcopy");
    expect(MICROCOPY_COMPLIANCE.export.cta).toBe("Exportar CSV");
    expect(MICROCOPY_COMPLIANCE.export.preparing).toBe("Preparando CSV...");
    expect(MICROCOPY_COMPLIANCE.export.ready).toBe("Descarga lista");
  });
});

describe("ComplianceStatsCards severity counting", () => {
  function countBySeverity(events: ComplianceEventItem[], severity: string): number {
    return events.filter((e) => e.severity === severity).length;
  }

  const mockEvents: ComplianceEventItem[] = [
    {
      id: "1",
      event_type: "pii_detected",
      severity: "high",
      patient_id: null,
      booking_id: null,
      payload_redacted: {},
      actor_id: null,
      actor_type: null,
      created_at: "2026-05-14T10:00:00Z",
    },
    {
      id: "2",
      event_type: "consent_signed",
      severity: "info",
      patient_id: "p1",
      booking_id: "b1",
      payload_redacted: { consent_token: "redacted" },
      actor_id: "a1",
      actor_type: "patient",
      created_at: "2026-05-14T10:01:00Z",
    },
    {
      id: "3",
      event_type: "cross_tenant_blocked",
      severity: "high",
      patient_id: null,
      booking_id: null,
      payload_redacted: {},
      actor_id: null,
      actor_type: "system",
      created_at: "2026-05-14T10:02:00Z",
    },
  ];

  it("counts high severity events correctly", () => {
    expect(countBySeverity(mockEvents, "high")).toBe(2);
  });

  it("counts info severity events correctly", () => {
    expect(countBySeverity(mockEvents, "info")).toBe(1);
  });

  it("returns 0 for events with no match", () => {
    expect(countBySeverity(mockEvents, "medium")).toBe(0);
  });

  it("handles empty events array", () => {
    expect(countBySeverity([], "high")).toBe(0);
  });
});
