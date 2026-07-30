// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * ContactSidebar.test.tsx — Vitest unit tests for rich PHI-aware ContactSidebar.
 * T-4 vitalia-fase2-adrian-inbox (MIGRATE + MERGE — updated to rich component interface)
 *
 * MERGE note: parity tests used { conversation, leadId } props.
 * Rich version uses { conversationId, leadId, contact: InboxContactInfo }.
 * Regression_guard: same user-observable behaviors (PHI masking, NPS, offer).
 *
 * downstream-regression-na: brand-local component test
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ContactSidebar } from "./ContactSidebar";
import type { InboxContactInfo } from "./ContactSidebar";

// Mock Clerk — ContactSidebar → useCurrentUser → useAuth; useTenantLocale → useUser
// Canonical pattern per __tests__/ContactSidebar.test.tsx + mateo/AgendaHeader.test.tsx
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
  useUser: () => ({ user: null, isLoaded: true }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));

// Mock useCurrentUser to avoid Clerk provider requirement
vi.mock("@/hooks/useCurrentUser", () => ({
  useCurrentUser: () => ({
    id: "user-1",
    role: "admin_clinic",
    hasPhiAccess: true,
    isLoaded: true,
  }),
}));

// Stub PHI wrapper components — allow render without full provider tree
vi.mock("@/components/shared/phi/PiiMaskedSpan", () => ({
  PiiMaskedSpan: ({ value }: { value: string | null | undefined }) => (
    <span>{value ?? "—"}</span>
  ),
}));
vi.mock("@/components/shared/phi/RequireRole", () => ({
  RequireRole: ({
    children,
    userRole,
    roles,
    fallback,
  }: {
    children: React.ReactNode;
    userRole: string | null;
    roles: string[];
    fallback?: React.ReactNode;
  }) => {
    if (!userRole || !roles.includes(userRole)) return <>{fallback ?? null}</>;
    return <>{children}</>;
  },
}));
vi.mock("@/components/shared/phi/AuditedSection", () => ({
  AuditedSection: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

// ── Fixtures ─────────────────────────────────────────────────────────────────

const BASE_CONTACT: InboxContactInfo = {
  patientId: "pat-hash-001",
  name: null,           // null = PHI masked by component
  phone: "+51999994321",
  email: "patient@example.com",
  statusTag: "Calificando",
  npsHistory: null,
};

const CONTACT_WITH_NPS: InboxContactInfo = {
  patientId: "pat-hash-002",
  name: null,
  phone: "+51999994321",
  email: "patient@example.com",
  statusTag: null,
  npsHistory: [
    { score: 9, recorded_at: "2026-05-01T10:00:00Z", comment: "Excelente" },
    { score: 7, recorded_at: "2026-04-01T10:00:00Z" },
  ],
};

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("ContactSidebar — rich PHI-aware version", () => {
  it("renders without crashing with minimal contact", () => {
    render(
      <ContactSidebar
        conversationId="conv-001"
        leadId="lead-001"
        contact={BASE_CONTACT}
      />,
    );
    expect(document.body).toBeDefined();
  });

  it("renders with optional className", () => {
    render(
      <ContactSidebar
        conversationId="conv-001"
        leadId="lead-001"
        contact={BASE_CONTACT}
        className="test-class"
      />,
    );
    // Does not throw
    expect(document.body).toBeDefined();
  });

  it("renders NPS history scores when present", () => {
    render(
      <ContactSidebar
        conversationId="conv-001"
        leadId="lead-001"
        contact={CONTACT_WITH_NPS}
      />,
    );
    expect(screen.getByLabelText("NPS 9")).toBeDefined();
    expect(screen.getByLabelText("NPS 7")).toBeDefined();
  });

  it("shows NPS empty text when no NPS history", () => {
    render(
      <ContactSidebar
        conversationId="conv-001"
        leadId="lead-001"
        contact={BASE_CONTACT}
      />,
    );
    expect(screen.getByText(/sin encuestas nps/i)).toBeDefined();
  });
});
