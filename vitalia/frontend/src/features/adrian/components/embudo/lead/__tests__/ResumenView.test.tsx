// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * ResumenView.test.tsx — component tests for ResumenView (U1/U2 fix).
 *
 * TDD: tests written to verify the U1/U2 fixes:
 *   U1: lead name shown as plain text (no data-phi wrapping, non_phi marketing)
 *   U2: phone and email shown in Datos del lead block
 *
 * These tests were RED with the old implementation (PiiMaskedSpan wrapping name,
 * Contacto row with masked name, no phone/email rows) and are GREEN with the fix.
 *
 * Mock strategy: mock useLeadDetail hook (returns LeadDetailLeadDTO shape),
 * mock useAuth/useTenantId/ScoreBreakdown to keep test isolated.
 * Does NOT mock ResumenView itself (tests the real component).
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

// -- Mocks ------------------------------------------------------------------

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));

vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: vi.fn().mockReturnValue("tenant-test"),
}));

vi.mock("@/hooks/useTenantLocale", () => ({
  useTenantLocale: vi.fn().mockReturnValue({ currency: "MXN", timezone: "America/Mexico_City" }),
}));

vi.mock("@/components/shared/shell-organism/ChannelBadge", () => ({
  ChannelBadge: ({ channel }: { channel: string }) => (
    <span data-testid="channel-badge">{channel}</span>
  ),
}));

vi.mock("../ScoreBreakdown", () => ({
  ScoreBreakdown: () => <div data-testid="score-breakdown" />,
}));

// Mock useLeadDetail — the key hook for this component
vi.mock("../../../../api/lead", () => ({
  useLeadDetail: vi.fn(),
}));

import { useLeadDetail } from "../../../../api/lead";
import { ResumenView } from "../ResumenView";

// -- Test fixtures -----------------------------------------------------------

const MOCK_LEAD_DETAIL_WITH_CONTACT = {
  lead: {
    id: "lead-001",
    tenantId: "tenant-test",
    name: "María García López",
    email: "maria@example.com",
    phone: "+52 55 1234 5678",
    source: "instagram",
    status: "active",
    createdAt: "2026-06-01T10:00:00Z",
    stage: "calificando" as const,
    score: 64,
    temperature: "warm" as const,
    operatedBy: "agent" as const,
    channel: "whatsapp",
    estimatedValue: 8000,
    currency: "MXN",
    serviceInterest: "Ortodoncia invisible",
    buyingSignals: ["urgencia"],
    stageEnteredAt: "2026-06-03T09:00:00Z",
    isFrozen: false,
    frozenReason: null,
    depositStatus: null,
    version: 1,
    assignedDoctorId: "doc-001",
  },
  scoreBreakdown: [{ label: "Preguntó precio", delta: 25, icon: null }],
  autonomy: {
    operatedBy: "agent",
    can: ["mover etapa", "agendar"],
    needsOk: ["cobrar"],
  },
};

const MOCK_LEAD_DETAIL_EMPTY_CONTACT = {
  lead: {
    ...MOCK_LEAD_DETAIL_WITH_CONTACT.lead,
    email: null,
    phone: null,
    assignedDoctorId: null,
  },
  scoreBreakdown: [],
  autonomy: {
    operatedBy: "agent",
    can: ["mover etapa"],
    needsOk: [],
  },
};

// -- Tests ------------------------------------------------------------------

describe("ResumenView — U1/U2 fix", () => {
  it("renders lead name as plain text (no PHI mask) in Datos del lead", () => {
    vi.mocked(useLeadDetail).mockReturnValue({
      data: MOCK_LEAD_DETAIL_WITH_CONTACT,
      isLoading: false,
      isError: false,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test mock partial shape
} as any);

    render(<ResumenView leadId="lead-001" tenantId="tenant-test" />);

    // Name must be rendered as plain text
    const nameEl = screen.getByTestId("lead-name");
    expect(nameEl).toBeInTheDocument();
    expect(nameEl).toHaveTextContent("María García López");

    // Name element must NOT have data-phi attribute (no PiiMaskedSpan wrapping)
    expect(nameEl).not.toHaveAttribute("data-phi");
  });

  it("renders phone in Datos del lead when present", () => {
    vi.mocked(useLeadDetail).mockReturnValue({
      data: MOCK_LEAD_DETAIL_WITH_CONTACT,
      isLoading: false,
      isError: false,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test mock partial shape
} as any);

    render(<ResumenView leadId="lead-001" tenantId="tenant-test" />);

    const phoneEl = screen.getByTestId("lead-phone");
    expect(phoneEl).toBeInTheDocument();
    expect(phoneEl).toHaveTextContent("+52 55 1234 5678");
  });

  it("renders email in Datos del lead when present", () => {
    vi.mocked(useLeadDetail).mockReturnValue({
      data: MOCK_LEAD_DETAIL_WITH_CONTACT,
      isLoading: false,
      isError: false,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test mock partial shape
} as any);

    render(<ResumenView leadId="lead-001" tenantId="tenant-test" />);

    const emailEl = screen.getByTestId("lead-email");
    expect(emailEl).toBeInTheDocument();
    expect(emailEl).toHaveTextContent("maria@example.com");
  });

  it("renders empty state for phone when null", () => {
    vi.mocked(useLeadDetail).mockReturnValue({
      data: MOCK_LEAD_DETAIL_EMPTY_CONTACT,
      isLoading: false,
      isError: false,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test mock partial shape
} as any);

    render(<ResumenView leadId="lead-001" tenantId="tenant-test" />);

    const phoneEl = screen.getByTestId("lead-phone");
    expect(phoneEl).toBeInTheDocument();
    expect(phoneEl).toHaveTextContent("Sin teléfono registrado");
  });

  it("renders empty state for email when null", () => {
    vi.mocked(useLeadDetail).mockReturnValue({
      data: MOCK_LEAD_DETAIL_EMPTY_CONTACT,
      isLoading: false,
      isError: false,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test mock partial shape
} as any);

    render(<ResumenView leadId="lead-001" tenantId="tenant-test" />);

    const emailEl = screen.getByTestId("lead-email");
    expect(emailEl).toBeInTheDocument();
    expect(emailEl).toHaveTextContent("Sin correo registrado");
  });

  it("shows loading skeleton while fetching", () => {
    vi.mocked(useLeadDetail).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test mock partial shape
} as any);

    render(<ResumenView leadId="lead-001" tenantId="tenant-test" />);

    // The loading skeleton has aria-busy="true" on the container
    const skeleton = document.querySelector('[aria-busy="true"]');
    expect(skeleton).toBeInTheDocument();
    // resumen-view must NOT exist during loading
    expect(screen.queryByTestId("resumen-view")).not.toBeInTheDocument();
  });

  it("shows error state on fetch failure", () => {
    vi.mocked(useLeadDetail).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test mock partial shape
} as any);

    render(<ResumenView leadId="lead-001" tenantId="tenant-test" />);

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.queryByTestId("resumen-view")).not.toBeInTheDocument();
  });

  it("renders full resumen-view with all blocks when data is present", () => {
    vi.mocked(useLeadDetail).mockReturnValue({
      data: MOCK_LEAD_DETAIL_WITH_CONTACT,
      isLoading: false,
      isError: false,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- test mock partial shape
} as any);

    render(<ResumenView leadId="lead-001" tenantId="tenant-test" />);

    expect(screen.getByTestId("resumen-view")).toBeInTheDocument();
    expect(screen.getByTestId("score-breakdown")).toBeInTheDocument();
  });
});
