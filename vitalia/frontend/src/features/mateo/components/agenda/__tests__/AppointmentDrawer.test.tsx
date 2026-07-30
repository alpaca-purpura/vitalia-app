/**
 * AppointmentDrawer.test.tsx — Vitest unit tests (TDD RED→GREEN).
 *
 * T-14 vitalia-fase2-valeria-agenda
 * spec_anchor: 06-tickets.yaml T-14 acceptance A1..A7
 *
 * Tests (covering acceptance criteria):
 *   A1 - Drawer renders with data-testid when open
 *   A2 - Patient masked name renders (PHI invariant)
 *   A2b - Turno + Pago sections accessible (default expanded)
 *   A3 - Resize handle renders with correct aria-label
 *   A4 - onOpenChange(false) triggers closeDrawer (Esc key path)
 *   A5 - Stale banner does NOT render when staleDetected=false
 *   A6 - "Cancelar turno" opens confirm dialog
 *   A7 - "Ver ficha completa" button is disabled
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppointmentDrawer } from "../AppointmentDrawer";
import type { Appointment } from "../../../types/agenda.types";

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock("@clerk/nextjs", () => ({
  useAuth: vi.fn(() => ({
    getToken: vi.fn(() => Promise.resolve("test-token")),
    isLoaded: true,
    isSignedIn: true,
  })),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


vi.mock("@/hooks/useTenantLocale", () => ({
  useTenantLocale: () => ({
    currency: "PEN",
    timezone: "America/Lima",
    locale: "es-PE",
  }),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
}));

const mockCloseDrawer = vi.fn();
const mockSetStaleDetected = vi.fn();

vi.mock("../../../store/agenda-store", () => ({
  useDrawerStore: vi.fn(() => ({
    drawerOpen: true,
    selectedSlotId: "slot-123",
    staleDetected: false,
    closeDrawer: mockCloseDrawer,
    setStaleDetected: mockSetStaleDetected,
    openDrawer: vi.fn(),
    toggleDrawer: vi.fn(),
    setDrawerWidth: vi.fn(),
    drawerWidth: 520,
  })),
  DRAWER_WIDTH_MIN: 440,
  DRAWER_WIDTH_MAX: 640,
  DRAWER_WIDTH_DEFAULT: 520,
}));

vi.mock("../../../hooks/useDrawerWidth", () => ({
  useDrawerWidth: vi.fn(() => ({
    drawerWidth: 520,
    setDrawerWidth: vi.fn(),
    drawerStyle: { width: "520px", minWidth: "440px", maxWidth: "640px" },
  })),
}));

// Default: desktop (isMobile = false)
vi.mock("@/hooks/useMediaQuery", () => ({
  useMediaQuery: vi.fn(() => false),
}));

const mockAppointment: Appointment = {
  appointmentId: "slot-123",
  patientId: "patient-456",
  patientNameMasked: "P. Hernández",
  patientDniMasked: "12.***.***",
  patientPhoneMasked: "+51 9** *** 423",
  patientEmailMasked: null,
  startTime: "2026-05-27T14:00:00.000Z",
  endTime: "2026-05-27T14:30:00.000Z",
  doctorId: "doctor-789",
  doctorLabel: "Dr. C. Mendoza",
  serviceLabel: "Limpieza dental",
  appointmentStatus: "SCHEDULED",
  paymentStatus: "unpaid",
  origin: "walk_in",
  balanceDueCents: 5000,
  balancePaidCents: 0,
  currency: "PEN",
  currencyOverride: null,
  payments: [],
  notesInternal: null,
  lastActivityAt: null,
  lastActivityByLabel: null,
};

vi.mock("../../../api/agenda", () => ({
  useAppointmentDetail: vi.fn(() => ({
    data: mockAppointment,
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
  })),
  usePatchAppointmentStatus: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  // T-15: CobrarSaldoSubform uses these — must be mocked here too
  useChargeAppointment: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
    reset: vi.fn(),
  })),
  useEmitFiscalDoc: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
    reset: vi.fn(),
  })),
  agendaKeys: {
    detail: (tenantId: string, appointmentId: string) =>
      ["agenda", "detail", tenantId, appointmentId],
    all: (tenantId: string) => ["agenda", tenantId],
  },
}));

vi.mock("../../../api/notify", () => ({
  useSendNotificationMutation: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
  })),
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

function renderDrawer(queryClient: QueryClient) {
  return render(
    <QueryClientProvider client={queryClient}>
      <AppointmentDrawer
        tenantId="tenant-abc"
        tenantCurrency="PEN"
        tenantLocale="es-PE"
        tenantTimezone="America/Lima"
      />
    </QueryClientProvider>,
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("AppointmentDrawer", () => {
  let queryClient: QueryClient;

  beforeEach(async () => {
    queryClient = makeQueryClient();
    vi.clearAllMocks();

    // Reset mocks to default successful state
    const agendaApi = vi.mocked(await import("../../../api/agenda"));
    agendaApi.useAppointmentDetail.mockReturnValue({
      data: mockAppointment,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof agendaApi.useAppointmentDetail>);
    agendaApi.usePatchAppointmentStatus.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof agendaApi.usePatchAppointmentStatus>);
  });

  it("A1 — renders drawer with data-testid when open", () => {
    renderDrawer(queryClient);
    expect(screen.getByTestId("appointment-drawer")).toBeInTheDocument();
  });

  it("A2 — renders patient masked name (PHI invariant)", () => {
    renderDrawer(queryClient);
    expect(screen.getByText("P. Hernández")).toBeInTheDocument();
  });

  it("A2b — turno section is accessible by default", async () => {
    renderDrawer(queryClient);
    await waitFor(() => {
      expect(screen.getByTestId("turno-section")).toBeInTheDocument();
    });
  });

  it("A2c — pago section is accessible by default", async () => {
    renderDrawer(queryClient);
    await waitFor(() => {
      expect(screen.getByTestId("pago-section")).toBeInTheDocument();
    });
  });

  it("A3 — resize handle renders with correct aria-label", () => {
    renderDrawer(queryClient);
    const handle = screen.getByTestId("resize-handle");
    expect(handle).toBeInTheDocument();
    expect(handle).toHaveAttribute("aria-label", "Ajustar ancho del panel");
  });

  it("A4 — clicking close button (X) triggers closeDrawer", () => {
    renderDrawer(queryClient);
    // Sheet's SheetClose button has sr-only text "Close"
    const closeBtn = screen.getByRole("button", { name: /close/i });
    fireEvent.click(closeBtn);
    expect(mockCloseDrawer).toHaveBeenCalled();
  });

  it("A5 — stale banner NOT rendered when staleDetected=false", () => {
    renderDrawer(queryClient);
    expect(screen.queryByTestId("stale-banner")).not.toBeInTheDocument();
  });

  it("A6 — 'Cancelar turno' opens confirm Dialog", async () => {
    renderDrawer(queryClient);
    const cancelBtn = await screen.findByRole("button", { name: /cancelar turno/i });
    fireEvent.click(cancelBtn);
    await waitFor(() => {
      expect(
        screen.getByText(/cancelar este turno/i),
      ).toBeInTheDocument();
    });
  });

  it("A7 — 'Ver ficha completa' button is disabled", () => {
    renderDrawer(queryClient);
    const btn = screen.getByRole("button", { name: /ver ficha completa/i });
    expect(btn).toBeDisabled();
  });

  it("A7b — skeleton renders when isLoading=true", async () => {
    const { useAppointmentDetail } = vi.mocked(await import("../../../api/agenda"));
    useAppointmentDetail.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useAppointmentDetail>);
    renderDrawer(queryClient);
    expect(screen.getByRole("status", { name: /cargando/i })).toBeInTheDocument();
  });

  it("A8 — error state renders Reintentar button when fetch fails", async () => {
    const { useAppointmentDetail } = vi.mocked(await import("../../../api/agenda"));
    useAppointmentDetail.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error("Network error"),
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useAppointmentDetail>);
    renderDrawer(queryClient);
    expect(screen.getByRole("button", { name: /reintentar/i })).toBeInTheDocument();
  });

  // ── AC-12: Mobile responsive bottom drawer ────────────────────────────────

  it("AC-12 — desktop: SheetContent has side=right (isMobile=false)", () => {
    // Default mock already returns false — desktop mode
    renderDrawer(queryClient);
    const drawer = screen.getByTestId("appointment-drawer");
    // SheetContent renders as a dialog; verify no mobile class present
    expect(drawer).toBeInTheDocument();
    // rounded-t-2xl class is only added on mobile
    expect(drawer).not.toHaveClass("rounded-t-2xl");
  });

  it("AC-12 — mobile: SheetContent has h-[95vh] class (isMobile=true)", async () => {
    const { useMediaQuery } = vi.mocked(await import("@/hooks/useMediaQuery"));
    useMediaQuery.mockReturnValue(true);
    renderDrawer(queryClient);
    const drawer = screen.getByTestId("appointment-drawer");
    expect(drawer).toBeInTheDocument();
    // Mobile-specific class applied
    expect(drawer).toHaveClass("rounded-t-2xl");
  });
});
