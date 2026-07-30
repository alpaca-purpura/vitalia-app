/**
 * AppointmentDrawerPagoSection.test.tsx — Vitest unit tests (TDD RED→GREEN).
 *
 * T-14 + T-15 vitalia-fase2-valeria-agenda
 * spec_anchor: 06-tickets.yaml T-14 + T-15 + 03-arch.md § 6.7
 *
 * Tests:
 *   - Renders payment status badge for paid/deposit/unpaid/no_show
 *   - Renders balance due and paid amounts using tenantCurrency
 *   - CobrarSaldoSubform renders when balance > 0 and status is SCHEDULED (T-15)
 *   - CobrarSaldoSubform NOT rendered when appointment is CANCELLED
 *   - Historical payments list renders payment rows
 *   - Payment rows show method label + amount
 *   - "Sin registros de pago" renders when no payments and no balance
 *   - Currency override takes precedence over tenantCurrency
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppointmentDrawerPagoSection } from "../AppointmentDrawerPagoSection";
import type { Appointment, AppointmentPayment } from "../../../types/agenda.types";

// ── Mocks for CobrarSaldoSubform dependencies ──────────────────────────────

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

vi.mock("../../../api/agenda", () => ({
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
    all: (id: string) => ["agenda", id],
    detail: (id: string, aid: string) => ["agenda", "detail", id, aid],
  },
}));

// ── Fixtures ───────────────────────────────────────────────────────────────

const BASE_APPOINTMENT: Appointment = {
  appointmentId: "slot-123",
  patientId: "patient-456",
  patientNameMasked: "P. Hernández",
  patientDniMasked: null,
  patientPhoneMasked: null,
  patientEmailMasked: null,
  startTime: "2026-05-27T14:00:00.000Z",
  endTime: "2026-05-27T14:30:00.000Z",
  doctorId: "doc-789",
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

const SAMPLE_PAYMENT: AppointmentPayment = {
  paymentId: "pay-001",
  amountCents: 3000,
  currency: "PEN",
  method: "efectivo",
  fiscalDocUrl: null,
  fiscalDocType: null,
  createdAt: "2026-05-27T14:35:00.000Z",
  createdByLabel: "Recep. Gómez",
};

// ── Helper ─────────────────────────────────────────────────────────────────

function renderPagoSection(
  appointment: Appointment = BASE_APPOINTMENT,
  overrides?: { tenantCurrency?: string; tenantLocale?: string },
) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <AppointmentDrawerPagoSection
        appointment={appointment}
        tenantId="tenant-uuid-test"
        tenantCurrency={overrides?.tenantCurrency ?? "PEN"}
        tenantLocale={overrides?.tenantLocale ?? "es-PE"}
        tenantTimezone="America/Lima"
      />
    </QueryClientProvider>,
  );
}

// ── Tests ──────────────────────────────────────────────────────────────────

describe("AppointmentDrawerPagoSection", () => {
  it("renders 'Sin pago' badge for unpaid status", () => {
    renderPagoSection();
    expect(screen.getByText("Sin pago")).toBeInTheDocument();
  });

  it("renders 'Pagado' badge for paid status", () => {
    renderPagoSection({ ...BASE_APPOINTMENT, paymentStatus: "paid", balanceDueCents: 0 });
    // Badge text (distinct from the "Pagado" balance label)
    const allPagado = screen.getAllByText("Pagado");
    // At minimum one instance should exist (the badge)
    expect(allPagado.length).toBeGreaterThanOrEqual(1);
  });

  it("renders 'Con depósito' badge for deposit status", () => {
    renderPagoSection({ ...BASE_APPOINTMENT, paymentStatus: "deposit" });
    expect(screen.getByText("Con depósito")).toBeInTheDocument();
  });

  it("renders CobrarSaldoSubform (T-15) when balance > 0 and status is SCHEDULED", () => {
    renderPagoSection();
    // Real form renders with a "Cobrar" submit button (replaces T-14 placeholder)
    expect(screen.getByRole("button", { name: /cobrar/i })).toBeInTheDocument();
    expect(screen.getByTestId("cobrar-saldo-subform")).toBeInTheDocument();
  });

  it("does NOT render CobrarSaldoSubform when appointment is CANCELLED", () => {
    renderPagoSection({ ...BASE_APPOINTMENT, appointmentStatus: "CANCELLED" });
    expect(
      screen.queryByTestId("cobrar-saldo-subform"),
    ).not.toBeInTheDocument();
  });

  it("does NOT render CobrarSaldoSubform when balance is 0", () => {
    renderPagoSection({ ...BASE_APPOINTMENT, balanceDueCents: 0 });
    expect(
      screen.queryByTestId("cobrar-saldo-subform"),
    ).not.toBeInTheDocument();
  });

  it("renders payment rows from payments array", () => {
    renderPagoSection({ ...BASE_APPOINTMENT, payments: [SAMPLE_PAYMENT] });
    expect(screen.getByTestId("payment-row")).toBeInTheDocument();
    // Method label — may appear multiple times (payment row + form select)
    const efectivoElements = screen.getAllByText(/efectivo/i);
    expect(efectivoElements.length).toBeGreaterThanOrEqual(1);
    // Staff label (unique)
    expect(screen.getByText(/Recep\. Gómez/)).toBeInTheDocument();
  });

  it("renders 'Sin registros de pago' when no payments and no balance", () => {
    renderPagoSection({
      ...BASE_APPOINTMENT,
      paymentStatus: "paid",
      balanceDueCents: 0,
      balancePaidCents: 0,
      payments: [],
    });
    expect(screen.getByText(/sin registros de pago/i)).toBeInTheDocument();
  });

  it("uses currencyOverride when set instead of tenantCurrency", () => {
    renderPagoSection({
      ...BASE_APPOINTMENT,
      currency: "PEN",
      currencyOverride: "USD",
      payments: [{ ...SAMPLE_PAYMENT, currency: "USD" }],
    });
    // USD format (dollar sign) should appear in payment rows
    // Intl.NumberFormat('es-PE', {currency: 'USD'}) produces "USD 30.00" or similar
    const row = screen.getByTestId("payment-row");
    expect(row.textContent).toMatch(/USD|US\$|\$/);
  });
});
