/**
 * CobrarSaldoSubform.saga.test.tsx — Saga integration tests.
 *
 * T-15 vitalia-fase2-valeria-agenda
 * spec_anchor: 06-tickets.yaml T-15 + 01-spec.md SC-1, SC-2, SC-5, SC-6
 *
 * Tests error saga paths:
 *   A5: Error 503 payment → ErrorAlert + retry button (same idempotencyKey)
 *   A6: Error 503 fiscal post-charge → Warning alert + standalone retry
 *   A7: Error 409 concurrent charge → "saldo ya cobrado" alert + collapse
 *
 * Note: these are unit saga tests using mocked mutations.
 * Full E2E saga requires Playwright (SC-1, SC-2, SC-5 — playwright_required: true).
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CobrarSaldoSubformErrorAlert } from "../CobrarSaldoSubformErrorAlert";
import type { ChargeErrorState } from "../CobrarSaldoSubform";

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

vi.mock("../../../api/agenda", () => ({
  useChargeAppointment: vi.fn(() => ({
    mutate: vi.fn(),
    mutateAsync: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
    reset: vi.fn(),
  })),
  useEmitFiscalDoc: vi.fn(() => ({
    mutate: vi.fn(),
    mutateAsync: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
    reset: vi.fn(),
  })),
  agendaKeys: {
    all: (tenantId: string) => ["agenda", tenantId],
    detail: (tenantId: string, id: string) => ["agenda", "detail", tenantId, id],
  },
}));

// ── Helpers ────────────────────────────────────────────────────────────────

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

function renderErrorAlert(
  errorState: ChargeErrorState,
  overrides?: {
    onRetry?: () => void;
    onRetryFiscal?: () => void;
    onDismiss?: () => void;
    isRetrying?: boolean;
    isFiscalRetrying?: boolean;
  },
) {
  const queryClient = makeQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <CobrarSaldoSubformErrorAlert
        errorState={errorState}
        onRetry={overrides?.onRetry ?? vi.fn()}
        onRetryFiscal={overrides?.onRetryFiscal ?? vi.fn()}
        onDismiss={overrides?.onDismiss ?? vi.fn()}
        isRetrying={overrides?.isRetrying ?? false}
        isFiscalRetrying={overrides?.isFiscalRetrying ?? false}
      />
    </QueryClientProvider>,
  );
}

// ── Tests ──────────────────────────────────────────────────────────────────

describe("CobrarSaldoSubformErrorAlert", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // A5: 503 payment adapter failure
  it("A5: renders destructive alert for 503 payment error", () => {
    renderErrorAlert({ type: "payment_failed", message: "Error del adaptador de pago" });
    expect(
      screen.getByRole("alert"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/no pudimos procesar el cobro/i),
    ).toBeInTheDocument();
  });

  it("A5: renders retry button for payment failure", () => {
    renderErrorAlert({ type: "payment_failed", message: "Error del adaptador de pago" });
    expect(
      screen.getByRole("button", { name: /reintentar/i }),
    ).toBeInTheDocument();
  });

  it("A5: calls onRetry when retry button is clicked", async () => {
    const onRetry = vi.fn();
    renderErrorAlert(
      { type: "payment_failed", message: "Error del adaptador de pago" },
      { onRetry },
    );
    await userEvent.click(screen.getByRole("button", { name: /reintentar/i }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  // A6: 503 fiscal post-charge (charge OK, fiscal failed)
  it("A6: renders warning alert for fiscal failure after successful charge", () => {
    renderErrorAlert({
      type: "fiscal_failed",
      message: "Cobro registrado, comprobante pendiente",
      paymentId: "pay-uuid-001",
      fiscalDocType: "boleta",
    });
    const alert = screen.getByRole("alert");
    expect(alert).toBeInTheDocument();
    expect(
      screen.getByText(/cobro registrado/i),
    ).toBeInTheDocument();
  });

  it("A6: renders standalone retry emit button for fiscal failure", () => {
    renderErrorAlert({
      type: "fiscal_failed",
      message: "Cobro registrado, comprobante pendiente",
      paymentId: "pay-uuid-001",
      fiscalDocType: "boleta",
    });
    expect(
      screen.getByRole("button", { name: /reintentar emisión/i }),
    ).toBeInTheDocument();
  });

  it("A6: calls onRetryFiscal when fiscal retry button is clicked", async () => {
    const onRetryFiscal = vi.fn();
    renderErrorAlert(
      {
        type: "fiscal_failed",
        message: "Cobro registrado, comprobante pendiente",
        paymentId: "pay-uuid-001",
        fiscalDocType: "boleta",
      },
      { onRetryFiscal },
    );
    await userEvent.click(
      screen.getByRole("button", { name: /reintentar emisión/i }),
    );
    expect(onRetryFiscal).toHaveBeenCalledOnce();
  });

  // A7: 409 concurrent charge conflict
  it("A7: renders 409 conflict alert with specific message", () => {
    renderErrorAlert({ type: "conflict_409", message: "El saldo ya fue cobrado" });
    expect(screen.getByRole("alert")).toBeInTheDocument();
    // Multiple elements contain "fue cobrado" (title + description) — use getAllByText
    const matches = screen.getAllByText(/ya fue cobrado/i);
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it("A7: renders dismiss button for 409 conflict (no retry button)", () => {
    renderErrorAlert({ type: "conflict_409", message: "El saldo ya fue cobrado" });
    // Should have dismiss, not retry
    expect(
      screen.getByRole("button", { name: /entendido|cerrar|ok/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /reintentar$/i }),
    ).not.toBeInTheDocument();
  });

  it("A7: calls onDismiss when dismiss button is clicked for 409", async () => {
    const onDismiss = vi.fn();
    renderErrorAlert(
      { type: "conflict_409", message: "El saldo ya fue cobrado" },
      { onDismiss },
    );
    await userEvent.click(
      screen.getByRole("button", { name: /entendido|cerrar|ok/i }),
    );
    expect(onDismiss).toHaveBeenCalledOnce();
  });

  // Generic server error
  it("renders generic error alert for 500 error", () => {
    renderErrorAlert({ type: "server_error", message: "Error del servidor" });
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  // Validation errors
  it("renders validation error with field details for 422", () => {
    renderErrorAlert({
      type: "validation_422",
      message: "El tipo de comprobante es requerido",
    });
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(
      screen.getByText(/tipo de comprobante es requerido/i),
    ).toBeInTheDocument();
  });

  // Loading state for retry
  it("shows loading text on retry button when isRetrying=true", () => {
    renderErrorAlert(
      { type: "payment_failed", message: "Error del adaptador de pago" },
      { isRetrying: true },
    );
    expect(screen.getByText(/reintentando/i)).toBeInTheDocument();
  });
});
