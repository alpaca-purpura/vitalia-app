/**
 * ContactSidebar.test.tsx — Unit tests for inbox ContactSidebar (PHI-aware fork).
 *
 * Tests (per 04-validators.yaml gherkin_coverage):
 *   - test_phi_masked_default: phone/email/name rendered via PiiMaskedSpan (masked)
 *   - test_marketing_role_hides_nps_history: marketing role → NPS section hidden
 *   - test_phi_reveal_triggers_audit_log: AuditedSection fires on mount (audit log)
 *
 * PHI hooks mocked: usePiiRoleGate, AuditedSection, PiiMaskedSpan.
 * useCurrentUser mocked to control role.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ContactSidebar } from "../ContactSidebar";
import { INBOX_COPY } from "../../../lib/copy";

// Mock Clerk — ContactSidebar calls useTenantLocale() → useUser()
// T-2 fix (2026-06-01): useTenantLocale now uses useUser (not useOrganization).
// user: null / isLoaded: true triggers vitalia default locale (ARS / America/Argentina/Buenos_Aires / es-419)
vi.mock("@clerk/nextjs", () => ({
  useUser: () => ({ user: null, isLoaded: true }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


// Track AuditedSection mount calls
const mockAuditFire = vi.fn();
vi.mock("@/components/shared/phi/AuditedSection", () => ({
  AuditedSection: ({
    children,
    resourceType,
    resourceId,
  }: {
    children: React.ReactNode;
    resourceType: string;
    resourceId: string;
  }) => {
    // Simulate firing audit on mount via useEffect equivalent — track it
    mockAuditFire({ resourceType, resourceId });
    return <>{children}</>;
  },
}));

// Track PiiMaskedSpan renders
const mockPiiMaskedCalls: Array<{
  value: string | null | undefined;
  fieldType: string;
}> = [];
vi.mock("@/components/shared/phi/PiiMaskedSpan", () => ({
  PiiMaskedSpan: ({
    value,
    fieldType,
  }: {
    value: string | null | undefined;
    fieldType: string;
  }) => {
    mockPiiMaskedCalls.push({ value, fieldType });
    return (
      <span data-testid={`pii-masked-${fieldType}`} data-masked="true">
        {fieldType === "name" ? "██████" : "•••••"}
      </span>
    );
  },
}));

// Track RequireRole usage
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
    if (!userRole || !roles.includes(userRole)) {
      return <>{fallback ?? null}</>;
    }
    return <>{children}</>;
  },
}));

// Mock useCurrentUser to control role in tests
let mockRole: string | null = "admin_clinic";
vi.mock("@/hooks/useCurrentUser", () => ({
  useCurrentUser: vi.fn(() => ({
    id: "user-1",
    role: mockRole,
    hasPhiAccess:
      mockRole !== null &&
      ["doctor", "nurse", "admin_clinic"].includes(mockRole),
    isLoaded: true,
    firstName: "Test",
    lastName: "User",
    email: "test@clinic.com",
  })),
}));

const defaultProps = {
  conversationId: "conv-1",
  leadId: "lead-1",
  contact: {
    patientId: "pat-uuid-1",
    name: "Juan García",
    phone: "+5491100000000",
    email: "juan@example.com",
    statusTag: "Interesado",
    npsHistory: [
      {
        score: 9,
        recorded_at: "2026-01-10T00:00:00Z",
        comment: "Excelente atención",
      },
    ],
  },
};

describe("ContactSidebar — test_phi_masked_default (PHI fields masked via PiiMaskedSpan)", () => {
  beforeEach(() => {
    mockRole = "admin_clinic";
    mockPiiMaskedCalls.length = 0;
    mockAuditFire.mockReset();
  });

  it("renders sidebar with aria-label from INBOX_COPY.contactSidebar.ariaLabel", () => {
    render(<ContactSidebar {...defaultProps} />);
    const sidebar = screen.getByRole("complementary");
    expect(sidebar.getAttribute("aria-label")).toBe(
      INBOX_COPY.contactSidebar.ariaLabel,
    );
  });

  it("phone value is rendered via PiiMaskedSpan with fieldType=phone", () => {
    render(<ContactSidebar {...defaultProps} />);
    const maskedPhone = screen.getByTestId("pii-masked-phone");
    expect(maskedPhone).toBeDefined();
    expect(maskedPhone.getAttribute("data-masked")).toBe("true");
  });

  it("email value is rendered via PiiMaskedSpan with fieldType=email", () => {
    render(<ContactSidebar {...defaultProps} />);
    const maskedEmail = screen.getByTestId("pii-masked-email");
    expect(maskedEmail).toBeDefined();
  });

  it("patient name is rendered via PiiMaskedSpan with fieldType=name", () => {
    render(<ContactSidebar {...defaultProps} />);
    const maskedName = screen.getByTestId("pii-masked-name");
    expect(maskedName).toBeDefined();
  });

  it("shows noPhone copy when phone is null", () => {
    render(
      <ContactSidebar
        {...defaultProps}
        contact={{ ...defaultProps.contact, phone: null }}
      />,
    );
    expect(screen.getByText(INBOX_COPY.contactSidebar.noPhone)).toBeDefined();
  });

  it("shows noEmail copy when email is null", () => {
    render(
      <ContactSidebar
        {...defaultProps}
        contact={{ ...defaultProps.contact, email: null }}
      />,
    );
    expect(screen.getByText(INBOX_COPY.contactSidebar.noEmail)).toBeDefined();
  });
});

describe("ContactSidebar — test_marketing_role_hides_nps_history", () => {
  beforeEach(() => {
    mockPiiMaskedCalls.length = 0;
    mockAuditFire.mockReset();
  });

  it("marketing role: NPS history section is completely hidden", () => {
    mockRole = "marketing";
    render(<ContactSidebar {...defaultProps} />);
    // NPS history section title should not be visible to marketing role
    expect(
      screen.queryByText(INBOX_COPY.contactSidebar.sectionNpsHistory),
    ).toBeNull();
  });

  it("doctor role: NPS history section is visible", () => {
    mockRole = "doctor";
    render(<ContactSidebar {...defaultProps} />);
    expect(
      screen.getByText(INBOX_COPY.contactSidebar.sectionNpsHistory),
    ).toBeDefined();
  });

  it("nurse role: NPS history section is visible", () => {
    mockRole = "nurse";
    render(<ContactSidebar {...defaultProps} />);
    expect(
      screen.getByText(INBOX_COPY.contactSidebar.sectionNpsHistory),
    ).toBeDefined();
  });

  it("admin_clinic role: NPS history section is visible", () => {
    mockRole = "admin_clinic";
    render(<ContactSidebar {...defaultProps} />);
    expect(
      screen.getByText(INBOX_COPY.contactSidebar.sectionNpsHistory),
    ).toBeDefined();
  });

  it("sales role: NPS history section is hidden", () => {
    mockRole = "sales";
    render(<ContactSidebar {...defaultProps} />);
    expect(
      screen.queryByText(INBOX_COPY.contactSidebar.sectionNpsHistory),
    ).toBeNull();
  });
});

describe("ContactSidebar — test_phi_reveal_triggers_audit_log (AuditedSection fires on mount)", () => {
  beforeEach(() => {
    mockRole = "admin_clinic";
    mockAuditFire.mockReset();
  });

  it("AuditedSection is used with resourceType=patient_profile", () => {
    render(<ContactSidebar {...defaultProps} />);
    expect(mockAuditFire).toHaveBeenCalledWith(
      expect.objectContaining({ resourceType: "patient_profile" }),
    );
  });

  it("AuditedSection is called with the patientId as resourceId", () => {
    render(<ContactSidebar {...defaultProps} />);
    expect(mockAuditFire).toHaveBeenCalledWith(
      expect.objectContaining({ resourceId: "pat-uuid-1" }),
    );
  });

  it("renders contact section heading", () => {
    render(<ContactSidebar {...defaultProps} />);
    expect(
      screen.getByText(INBOX_COPY.contactSidebar.sectionContact),
    ).toBeDefined();
  });
});
