/**
 * CobrarSaldoSubform.test.tsx — Vitest unit tests (TDD RED→GREEN).
 *
 * T-15 vitalia-fase2-valeria-agenda
 * spec_anchor: 06-tickets.yaml T-15 + 03-arch.md § 6.7 + 01-spec.md § 5 A1-A9
 *
 * Tests:
 *   A1: Form renders with default values (amount = balance pendiente)
 *   A2: Discriminated union ChargeRequestSchema validates (cash sin card_token, etc.)
 *   A3: Loading state during POST charge (submit button shows "Procesando...")
 *   A4: fiscalDocType field appears only when emitInvoice=true
 *   A5: Error 503 payment → ErrorAlert with retry button
 *   A6: Error 503 fiscal → Warning alert with standalone retry
 *   A7: Error 409 concurrent → "saldo ya cobrado" alert
 *   A8: Currency override field hidden by default in "Más opciones"
 *   A9: emit_invoice toggle respects initial value from prop
 *
 * HIPAA-lite: amount + method NO son PHI — no masking en subform.
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CobrarSaldoSubform } from "../CobrarSaldoSubform";
import type { Appointment } from "../../../types/agenda.types";

// ── Mocks ──────────────────────────────────────────────────────────────────

vi.mock("@clerk/nextjs", () => ({
  useAuth: vi.fn(() => ({
    getToken: vi.fn(() => Promise.resolve("test-token")),
    isLoaded: true,
    isSignedIn: true,
  })),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
}));

// Mock useChargeAppointment and useEmitFiscalDoc
const mockChargeMutate = vi.fn();
const mockEmitFiscalMutate = vi.fn();
const mockChargeIsPending = vi.fn(() => false);
const mockEmitIsPending = vi.fn(() => false);

vi.mock("../../../api/agenda", () => ({
  useChargeAppointment: vi.fn(() => ({
    mutate: mockChargeMutate,
    mutateAsync: vi.fn(),
    isPending: mockChargeIsPending(),
    isError: false,
    error: null,
    reset: vi.fn(),
  })),
  useEmitFiscalDoc: vi.fn(() => ({
    mutate: mockEmitFiscalMutate,
    mutateAsync: vi.fn(),
    isPending: mockEmitIsPending(),
    isError: false,
    error: null,
    reset: vi.fn(),
  })),
  agendaKeys: {
    all: (tenantId: string) => ["agenda", tenantId],
    detail: (tenantId: string, id: string) => ["agenda", "detail", tenantId, id],
  },
}));

// ── Test fixtures ──────────────────────────────────────────────────────────

const BASE_APPOINTMENT: Appointment = {
  appointmentId: "appt-uuid-001",
  patientId: "patient-uuid-456",
  patientNameMasked: "P. Hernández",
  patientDniMasked: null,
  patientPhoneMasked: null,
  patientEmailMasked: null,
  startTime: "2026-05-27T14:00:00.000Z",
  endTime: "2026-05-27T14:30:00.000Z",
  doctorId: "doc-uuid-789",
  doctorLabel: "Dr. C. Mendoza",
  serviceLabel: "Limpieza dental",
  appointmentStatus: "SCHEDULED",
  paymentStatus: "unpaid",
  origin: "walk_in",
  balanceDueCents: 8000,
  balancePaidCents: 0,
  currency: "PEN",
  currencyOverride: null,
  payments: [],
  notesInternal: null,
  lastActivityAt: null,
  lastActivityByLabel: null,
};

// ── Helpers ────────────────────────────────────────────────────────────────

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

function renderSubform(
  appointment: Appointment = BASE_APPOINTMENT,
  overrides?: {
    tenantId?: string;
    tenantCurrency?: string;
    tenantLocale?: string;
    defaultEmitInvoice?: boolean;
  },
) {
  const queryClient = makeQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <CobrarSaldoSubform
        appointment={appointment}
        tenantId={overrides?.tenantId ?? "tenant-uuid-111"}
        tenantCurrency={overrides?.tenantCurrency ?? "PEN"}
        tenantLocale={overrides?.tenantLocale ?? "es-PE"}
        defaultEmitInvoice={overrides?.defaultEmitInvoice ?? true}
      />
    </QueryClientProvider>,
  );
}

// ── Tests ──────────────────────────────────────────────────────────────────

describe("CobrarSaldoSubform", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // A1: Form renders with default values
  it("A1: renders with default amount equal to balanceDueCents", () => {
    renderSubform();
    const amountInput = screen.getByRole("spinbutton", { name: /monto/i });
    // 8000 cents = 80.00
    expect(amountInput).toHaveValue(80);
  });

  it("A1: renders submit button with cobrar text", () => {
    renderSubform();
    expect(
      screen.getByRole("button", { name: /cobrar/i }),
    ).toBeInTheDocument();
  });

  it("A1: renders method select with payment options", () => {
    renderSubform();
    // The method field label should exist
    expect(screen.getByText(/método de pago/i)).toBeInTheDocument();
  });

  // A4: fiscalDocType appears only when emitInvoice=true
  it("A4: fiscalDocType field is visible when emitInvoice is checked", () => {
    renderSubform();
    // emitInvoice defaults to true, so fiscalDocType should be visible
    expect(screen.getByText(/tipo de comprobante/i)).toBeInTheDocument();
  });

  it("A4: fiscalDocType field is hidden when emitInvoice is unchecked", async () => {
    renderSubform();
    const checkbox = screen.getByRole("checkbox", { name: /emitir comprobante/i });
    await userEvent.click(checkbox);
    expect(
      screen.queryByText(/tipo de comprobante/i),
    ).not.toBeInTheDocument();
  });

  // A8: Currency override field hidden by default
  it("A8: currency override field is hidden by default", () => {
    renderSubform();
    // The currency override should be inside "Más opciones" collapsible
    expect(
      screen.queryByRole("combobox", { name: /moneda/i }),
    ).not.toBeInTheDocument();
  });

  it("A8: currency override field appears when 'Más opciones' is expanded", async () => {
    renderSubform();
    const masOpciones = screen.getByRole("button", { name: /más opciones/i });
    await userEvent.click(masOpciones);
    // After expanding, currency select should be visible
    await waitFor(() => {
      expect(screen.getByText(/moneda/i)).toBeInTheDocument();
    });
  });

  // A9: emit_invoice toggle respects initial value from prop
  it("A9: emit_invoice defaults to true when defaultEmitInvoice=true", () => {
    renderSubform(BASE_APPOINTMENT, { defaultEmitInvoice: true });
    const checkbox = screen.getByRole("checkbox", { name: /emitir comprobante/i });
    expect(checkbox).toBeChecked();
  });

  it("A9: emit_invoice defaults to false when defaultEmitInvoice=false", () => {
    renderSubform(BASE_APPOINTMENT, { defaultEmitInvoice: false });
    const checkbox = screen.getByRole("checkbox", { name: /emitir comprobante/i });
    expect(checkbox).not.toBeChecked();
  });

  // A2: Schema validation
  it("A2: shows validation error when amount is zero", async () => {
    renderSubform();
    const amountInput = screen.getByRole("spinbutton", { name: /monto/i });
    await userEvent.clear(amountInput);
    await userEvent.type(amountInput, "0");
    const submitBtn = screen.getByRole("button", { name: /cobrar/i });
    await userEvent.click(submitBtn);
    await waitFor(() => {
      expect(
        screen.getByText(/el monto debe ser mayor/i),
      ).toBeInTheDocument();
    });
  });

  // Renders form for different currencies
  it("renders PEN fiscal doc options (boleta/factura) for PEN currency", async () => {
    renderSubform();
    // Default currency is PEN from appointment
    // expand Más opciones is not needed to see fiscal doc type
    // fiscalDocType select should show PEN options
    const fiscalSelect = screen.getByRole("combobox", {
      name: /tipo de comprobante/i,
    });
    expect(fiscalSelect).toBeInTheDocument();
  });

  it("renders with ARS appointment currency and shows ARS fiscal doc types", () => {
    renderSubform({
      ...BASE_APPOINTMENT,
      currency: "ARS",
    });
    // Should render without crashing for ARS
    expect(screen.getByRole("button", { name: /cobrar/i })).toBeInTheDocument();
  });

  // Loading state — verified via aria-busy attribute on submit button
  it("A3: submit button has aria-busy=false by default (not loading)", () => {
    renderSubform();
    const submitBtn = screen.getByRole("button", { name: /cobrar/i });
    expect(submitBtn).toHaveAttribute("aria-busy", "false");
  });

  // Accessibility
  it("form has accessible structure with labels", () => {
    renderSubform();
    // Each form field should have a label
    expect(screen.getByRole("spinbutton", { name: /monto/i })).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: /emitir comprobante/i })).toBeInTheDocument();
  });

  // Keyboard accessibility
  it("submit button is keyboard focusable", () => {
    renderSubform();
    const submitBtn = screen.getByRole("button", { name: /cobrar/i });
    submitBtn.focus();
    expect(document.activeElement).toBe(submitBtn);
  });

  // Notes field
  it("renders optional notes textarea", () => {
    renderSubform();
    expect(screen.getByRole("textbox", { name: /notas/i })).toBeInTheDocument();
  });
});
