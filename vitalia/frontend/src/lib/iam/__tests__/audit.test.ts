/**
 * lib/iam/audit.ts unit tests — F1-S9 T-2 (TDD RED-first per tdd-mandatory.md)
 *
 * SC-4 / SC-8 gherkin coverage:
 *   - logCrossTenantAttempt captures payload via console.warn spy
 *   - logNoTenantsAssigned captures payload via console.warn spy
 *
 * Transport F1-S9: console.warn (backend audit endpoint = F2 Fase 2 scope).
 * HIPAA-lite: payload includes ONLY userId + attemptedTenant + timestamp. NO PHI.
 *
 * spec_anchor: 06-tickets.yaml T-2 gherkin_coverage + 04-validators.yaml val-fe-vitest-unit-audit-helper
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { logCrossTenantAttempt, logNoTenantsAssigned } from "../audit";

describe("logCrossTenantAttempt — audit event (SC-4)", () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
  });

  afterEach(() => {
    warnSpy.mockRestore();
  });

  it("calls console.warn with [audit] prefix", () => {
    logCrossTenantAttempt({
      userId: "user-abc",
      attemptedTenant: "tenant-xyz",
    });

    expect(warnSpy).toHaveBeenCalledOnce();
    const [firstArg] = warnSpy.mock.calls[0] ?? [];
    expect(String(firstArg)).toContain("[audit]");
  });

  it("payload includes action=cross_tenant_attempt", () => {
    logCrossTenantAttempt({
      userId: "user-abc",
      attemptedTenant: "tenant-xyz",
    });

    const [, payloadArg] = warnSpy.mock.calls[0] ?? [];
    const payload = payloadArg as Record<string, unknown>;
    expect(payload).toBeDefined();
    expect(payload["action"]).toBe("cross_tenant_attempt");
  });

  it("payload includes userId verbatim", () => {
    const userId = "user-hipaa-test";
    logCrossTenantAttempt({ userId, attemptedTenant: "tenant-xyz" });

    const [, payloadArg] = warnSpy.mock.calls[0] ?? [];
    const payload = payloadArg as Record<string, unknown>;
    expect(payload["userId"]).toBe(userId);
  });

  it("payload includes attemptedTenant verbatim", () => {
    const attemptedTenant = "clinic-b-456";
    logCrossTenantAttempt({ userId: "user-abc", attemptedTenant });

    const [, payloadArg] = warnSpy.mock.calls[0] ?? [];
    const payload = payloadArg as Record<string, unknown>;
    expect(payload["attemptedTenant"]).toBe(attemptedTenant);
  });

  it("payload includes timestamp (ISO 8601 string)", () => {
    logCrossTenantAttempt({
      userId: "user-abc",
      attemptedTenant: "tenant-xyz",
    });

    const [, payloadArg] = warnSpy.mock.calls[0] ?? [];
    const payload = payloadArg as Record<string, unknown>;
    expect(typeof payload["timestamp"]).toBe("string");
    // ISO 8601 format check
    expect(new Date(payload["timestamp"] as string).toISOString()).toBeTruthy();
  });

  it("HIPAA-lite: payload does NOT include PHI fields (no diagnosis, no patient name, no medical data)", () => {
    logCrossTenantAttempt({
      userId: "user-abc",
      attemptedTenant: "tenant-xyz",
    });

    const [, payloadArg] = warnSpy.mock.calls[0] ?? [];
    const payload = payloadArg as Record<string, unknown>;
    const payloadKeys = Object.keys(payload);

    const phiFields = [
      "diagnosis",
      "treatment",
      "medication",
      "patientName",
      "patient_name",
      "dni",
      "cuit",
      "phone",
      "email",
      "address",
    ];
    for (const field of phiFields) {
      expect(
        payloadKeys,
        `Payload must NOT contain PHI field: ${field}`,
      ).not.toContain(field);
    }
  });
});

describe("logNoTenantsAssigned — audit event (SC-8)", () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
  });

  afterEach(() => {
    warnSpy.mockRestore();
  });

  it("calls console.warn with [audit] prefix", () => {
    logNoTenantsAssigned({ userId: "user-no-clinics" });

    expect(warnSpy).toHaveBeenCalledOnce();
    const [firstArg] = warnSpy.mock.calls[0] ?? [];
    expect(String(firstArg)).toContain("[audit]");
  });

  it("payload includes action=no_tenants_assigned", () => {
    logNoTenantsAssigned({ userId: "user-no-clinics" });

    const [, payloadArg] = warnSpy.mock.calls[0] ?? [];
    const payload = payloadArg as Record<string, unknown>;
    expect(payload["action"]).toBe("no_tenants_assigned");
  });

  it("payload includes userId verbatim", () => {
    const userId = "user-without-tenant";
    logNoTenantsAssigned({ userId });

    const [, payloadArg] = warnSpy.mock.calls[0] ?? [];
    const payload = payloadArg as Record<string, unknown>;
    expect(payload["userId"]).toBe(userId);
  });

  it("payload includes timestamp (ISO 8601 string)", () => {
    logNoTenantsAssigned({ userId: "user-no-clinics" });

    const [, payloadArg] = warnSpy.mock.calls[0] ?? [];
    const payload = payloadArg as Record<string, unknown>;
    expect(typeof payload["timestamp"]).toBe("string");
    expect(new Date(payload["timestamp"] as string).toISOString()).toBeTruthy();
  });

  it("HIPAA-lite: payload does NOT include PHI fields", () => {
    logNoTenantsAssigned({ userId: "user-no-clinics" });

    const [, payloadArg] = warnSpy.mock.calls[0] ?? [];
    const payload = payloadArg as Record<string, unknown>;
    const payloadKeys = Object.keys(payload);

    const phiFields = [
      "diagnosis",
      "treatment",
      "medication",
      "patientName",
      "patient_name",
    ];
    for (const field of phiFields) {
      expect(
        payloadKeys,
        `Payload must NOT contain PHI field: ${field}`,
      ).not.toContain(field);
    }
  });
});
