// cap: iam.luana-core-adoption
// story-origin: vitalia-fe-tenant-resolution-no-clerk-org (T-2)
/**
 * audited-section.test.tsx — TDD RED → GREEN (T-2 2026-06-01)
 *
 * Verifies AuditedSection HIPAA-lite compliance:
 * 1. When tenantId is valid, fires audit log POST with X-Tenant-ID = our UUID
 * 2. When tenantId is null (Clerk org borrada), does NOT fire audit (safe guard)
 * 3. When userId is null, does NOT fire audit
 * 4. Renders children regardless of audit state
 * 5. Does NOT import or call useOrganization
 * 6. Uses useTenantId() (our hook), NOT useOrganization().organization.id
 *
 * Per vitalia/.claude/rules/hipaa-lite.md:
 *   Audit log is OBLIGATORY for all PHI reads. The fix must ensure audit fires
 *   with our real tenant UUID (not Clerk org id which became null after org deletion).
 *
 * Per MEMORY.md::no-clerk-organizations: no Clerk org APIs in FE components.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, waitFor } from "@testing-library/react";
import React from "react";

// ---------------------------------------------------------------------------
// Mock @clerk/nextjs — provide ONLY what AuditedSection should use post T-2 fix.
// useOrganization is NOT in the mock — proves AuditedSection does NOT call it.
// ---------------------------------------------------------------------------
const mockUseAuth = vi.fn();
const mockUseTenantId = vi.fn();
const mockUseClinicId = vi.fn();

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => mockUseAuth(),
  // useOrganization intentionally ABSENT — if AuditedSection calls it, vitest
  // will throw "useOrganization is not a function", proving the fix is needed.
}));

vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: () => mockUseTenantId(),
}));

vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: () => mockUseClinicId(),
}));

// ---------------------------------------------------------------------------
// Mock fetch — intercept audit log POST calls
// ---------------------------------------------------------------------------
const mockFetch = vi.fn();
global.fetch = mockFetch;

// ---------------------------------------------------------------------------
// Import AFTER mocks are set up (important for module resolution)
// ---------------------------------------------------------------------------
import { AuditedSection } from "@/components/shared/phi/AuditedSection";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const VALID_TENANT_UUID = "e69a691d-070e-5caf-a053-6e74642ec100";
const VALID_TOKEN = "mock-bearer-token";
const VALID_USER_ID = "user_abc123";
const VALID_CLINIC_ID = "clinic-uuid-456";

function setupValidAuth() {
  mockUseAuth.mockReturnValue({
    getToken: vi.fn().mockResolvedValue(VALID_TOKEN),
    userId: VALID_USER_ID,
  });
  mockUseTenantId.mockReturnValue(VALID_TENANT_UUID);
  mockUseClinicId.mockReturnValue(VALID_CLINIC_ID);
  mockFetch.mockResolvedValue({ ok: true });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("AuditedSection — T-2 fix: uses useTenantId() instead of useOrganization()", () => {
  beforeEach(() => {
    mockUseAuth.mockReset();
    mockUseTenantId.mockReset();
    mockUseClinicId.mockReset();
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  it("renders children regardless of audit state", () => {
    setupValidAuth();
    const { getByTestId } = render(
      <AuditedSection resourceType="patient_profile" resourceId="patient-uuid-001">
        <span data-testid="phi-content">Contenido PHI</span>
      </AuditedSection>,
    );
    expect(getByTestId("phi-content")).toBeTruthy();
  });

  it("fires audit log POST with X-Tenant-ID = our UUID when tenantId is valid", async () => {
    setupValidAuth();

    render(
      <AuditedSection
        resourceType="patient_profile"
        resourceId="patient-uuid-001"
        action="view"
      >
        <span>PHI</span>
      </AuditedSection>,
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    const [url, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/vitalia/audit-log");
    expect(options.method).toBe("POST");

    // CRITICAL: X-Tenant-ID must be our UUID, NOT a Clerk org id
    const headers = options.headers as Record<string, string>;
    expect(headers["X-Tenant-ID"]).toBe(VALID_TENANT_UUID);
    expect(headers["X-Tenant-ID"]).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    ); // must be UUID format
    expect(headers["X-Tenant-ID"]).not.toMatch(/^org_/); // must NOT be Clerk org format
  });

  it("includes Authorization header with Bearer token", async () => {
    setupValidAuth();

    render(
      <AuditedSection resourceType="patient_profile" resourceId="patient-uuid-001">
        <span>PHI</span>
      </AuditedSection>,
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    const headers = options.headers as Record<string, string>;
    expect(headers["Authorization"]).toBe(`Bearer ${VALID_TOKEN}`);
  });

  it("includes X-Clinic-ID header when clinicId is available", async () => {
    setupValidAuth();

    render(
      <AuditedSection resourceType="patient_profile" resourceId="patient-uuid-001">
        <span>PHI</span>
      </AuditedSection>,
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    const headers = options.headers as Record<string, string>;
    expect(headers["X-Clinic-ID"]).toBe(VALID_CLINIC_ID);
  });

  it("does NOT fire audit when tenantId is null (Clerk org borrada → guard prevents broken audit)", async () => {
    // This is the critical HIPAA-lite constraint:
    // With org borrada, organization?.id was null → audit silently never fired.
    // New behavior: tenantId null → explicit guard → NO fire (correct: no broken data sent)
    // The audit must be triggered only when we have a real tenant UUID.
    mockUseAuth.mockReturnValue({
      getToken: vi.fn().mockResolvedValue(VALID_TOKEN),
      userId: VALID_USER_ID,
    });
    mockUseTenantId.mockReturnValue(null); // tenantId not resolved yet
    mockUseClinicId.mockReturnValue(VALID_CLINIC_ID);

    render(
      <AuditedSection resourceType="patient_profile" resourceId="patient-uuid-001">
        <span>PHI</span>
      </AuditedSection>,
    );

    // Give async effects time to potentially run
    await new Promise((resolve) => setTimeout(resolve, 50));

    // Audit must NOT fire when tenantId is null
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("does NOT fire audit when userId is null (user not authenticated)", async () => {
    mockUseAuth.mockReturnValue({
      getToken: vi.fn().mockResolvedValue(null),
      userId: null, // not authenticated
    });
    mockUseTenantId.mockReturnValue(VALID_TENANT_UUID);
    mockUseClinicId.mockReturnValue(null);

    render(
      <AuditedSection resourceType="patient_profile" resourceId="patient-uuid-001">
        <span>PHI</span>
      </AuditedSection>,
    );

    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("includes correct body with action, resourceType, resourceId, userId", async () => {
    setupValidAuth();

    render(
      <AuditedSection
        resourceType="treatment_record"
        resourceId="treatment-uuid-789"
        action="download"
      >
        <span>PHI</span>
      </AuditedSection>,
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(options.body as string) as Record<string, unknown>;
    expect(body.action).toBe("download");
    expect(body.resourceType).toBe("treatment_record");
    expect(body.resourceId).toBe("treatment-uuid-789");
    expect(body.userId).toBe(VALID_USER_ID);
  });

  it("only fires audit once even if component re-renders (auditFired.current guard)", async () => {
    setupValidAuth();

    const { rerender } = render(
      <AuditedSection resourceType="patient_profile" resourceId="patient-uuid-001">
        <span>PHI</span>
      </AuditedSection>,
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    // Re-render should NOT fire another audit
    rerender(
      <AuditedSection resourceType="patient_profile" resourceId="patient-uuid-001">
        <span>PHI updated</span>
      </AuditedSection>,
    );

    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it("renders children even when audit fetch fails (silent fail — non-blocking per hipaa-lite.md)", async () => {
    mockUseAuth.mockReturnValue({
      getToken: vi.fn().mockResolvedValue(VALID_TOKEN),
      userId: VALID_USER_ID,
    });
    mockUseTenantId.mockReturnValue(VALID_TENANT_UUID);
    // ★ 2026-06-11 (auditor): clinicId VÁLIDO — el componente exige dual-filter
    // tenant+clinic (hipaa-lite) y con null hace early-return SIN fetchear; este
    // test prueba el silent-fail DEL FETCH, así que el fetch debe disparar.
    mockUseClinicId.mockReturnValue(VALID_CLINIC_ID);
    mockFetch.mockRejectedValue(new Error("Network error"));

    const { getByTestId } = render(
      <AuditedSection resourceType="patient_profile" resourceId="patient-uuid-001">
        <span data-testid="phi-content">PHI content</span>
      </AuditedSection>,
    );

    // Await the failed fetch
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    // Children must still render despite audit failure
    expect(getByTestId("phi-content")).toBeTruthy();
  });
});
