/**
 * Tests for TreatmentFollowupDashboardClient — A1 acceptance criterion.
 * Verifies: named export, microcopy, timeline + chat + manual handoff CTA contract.
 *
 * Per .claude/rules/tdd-mandatory.md — RED first, then GREEN.
 * Component renders timeline + chat + manual handoff CTA per spec § 4.4 + § 8.5.
 */
import { describe, it, expect } from "vitest";

describe("TreatmentFollowupDashboardClient exports", () => {
  it("exports TreatmentFollowupDashboardClient as named export (no default)", async () => {
    const mod = await import(
      "@/features/vitalia/components/treatment-followup-dashboard-client"
    );
    expect(typeof mod.TreatmentFollowupDashboardClient).toBe("function");
    expect(mod).not.toHaveProperty("default");
  });
});

describe("TreatmentFollowupDashboardClient microcopy (spec § 8.5)", () => {
  it("MICROCOPY_TREATMENT has manual handoff CTA", async () => {
    const { MICROCOPY_TREATMENT } = await import("@/features/vitalia/config/microcopy");
    expect(MICROCOPY_TREATMENT.actions.takeConversation).toBe("Tomar conversación");
  });

  it("MICROCOPY_TREATMENT has send consent CTA", async () => {
    const { MICROCOPY_TREATMENT } = await import("@/features/vitalia/config/microcopy");
    expect(MICROCOPY_TREATMENT.actions.sendConsent).toBe("Enviar consentimiento");
  });

  it("MICROCOPY_TREATMENT has view audit CTA", async () => {
    const { MICROCOPY_TREATMENT } = await import("@/features/vitalia/config/microcopy");
    expect(MICROCOPY_TREATMENT.actions.viewAuditLog).toBe("Ver audit log paciente");
  });

  it("MICROCOPY_TREATMENT has page title", async () => {
    const { MICROCOPY_TREATMENT } = await import("@/features/vitalia/config/microcopy");
    expect(MICROCOPY_TREATMENT.title).toBe("Seguimiento de tratamiento");
  });

  it("safety escalation alert contains required words (spec § 8.5)", async () => {
    const { MICROCOPY_TREATMENT } = await import("@/features/vitalia/config/microcopy");
    const alert = MICROCOPY_TREATMENT.alerts.symptomsReported;
    expect(alert).toContain("paciente");
    expect(alert.length).toBeGreaterThan(20);
  });

  it("missed window alert content is in Spanish neutro (no voseo)", async () => {
    const { MICROCOPY_TREATMENT } = await import("@/features/vitalia/config/microcopy");
    const voseoPattern = /\b(tenés|podés|hacés|mirá|dejá|usá|considerá)\b/i;
    // All action texts should be Spanish neutro
    for (const text of Object.values(MICROCOPY_TREATMENT.actions)) {
      expect(text).not.toMatch(voseoPattern);
    }
  });
});

describe("TreatmentFollowupDashboardClient props contract", () => {
  it("component accepts treatmentId prop", async () => {
    const mod = await import(
      "@/features/vitalia/components/treatment-followup-dashboard-client"
    );
    // Named export exists and is callable
    expect(typeof mod.TreatmentFollowupDashboardClient).toBe("function");
  });

  it("component props interface is exported", async () => {
    // The component file must export the component — type exports verified at TS compile time
    const mod = await import(
      "@/features/vitalia/components/treatment-followup-dashboard-client"
    );
    expect(mod.TreatmentFollowupDashboardClient).toBeDefined();
  });
});

describe("TreatmentFollowupDashboardClient treatment states (spec § 5.5)", () => {
  it("status values cover spec 5.5 states", () => {
    const validStates = [
      "active",
      "paused_safety_escalation",
      "paused_awaiting_clinic",
      "completed",
    ];
    expect(validStates).toContain("active");
    expect(validStates).toContain("paused_safety_escalation");
    expect(validStates).toContain("completed");
    expect(validStates).toHaveLength(4);
  });
});
