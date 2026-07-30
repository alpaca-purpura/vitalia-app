// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-R-planpago
/**
 * PlanPagoView.test.tsx — Leaf 4 unit tests (3-cobro wired model).
 *
 * Covers:
 *   (a) Loading skeleton while data loads
 *   (b) Enabled fields render (not disabled/placeholder stubs)
 *   (c) Hydration from servicio.pricing (RHF `values` pattern, G2-F6)
 *   (d) Seeded defaults when servicio.pricing is null
 *   (e) Calculated fields (advance_equiv, per_month) display correctly
 *   (f) Patch behavior (dual-sync price, complete pricing object on non-price patch)
 *   (g) FloatingAutosaveIndicator present once (canon §2.6)
 *   (h) Currency fallback to locale when servicio.currency is null
 *
 * spec_anchor: 01-spec.md §Workspace Pestaña 4 · mockups/servicio-workspace.html §PLAN DE PAGO
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import type { ServiceDetail, ThreeChargePricing } from "../../../../types/servicios.types";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn(), isLoaded: true, isSignedIn: true }),
}));

vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: () => "tenant-abc",
}));

vi.mock("@/hooks/useTenantLocale", () => ({
  useTenantLocale: () => ({ currency: "MXN", locale: "es-MX" }),
}));

const mockSchedule = vi.fn();
vi.mock("@/hooks/use-autosave", () => ({
  useAutosave: () => ({ schedule: mockSchedule, status: "idle", flush: vi.fn() }),
}));

const mockMutateAsync = vi.fn().mockResolvedValue({});
const mockUseServicioDetail = vi.fn();
vi.mock("../../../../api/servicios", () => ({
  useServicioDetail: () => mockUseServicioDetail(),
  usePatchField: () => ({ mutateAsync: mockMutateAsync }),
}));

vi.mock("@luana/ui-kit", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@luana/ui-kit")>();
  return {
    ...actual,
    FloatingAutosaveIndicator: ({ status }: { status: string }) => (
      <div data-testid="floating-autosave" data-status={status} />
    ),
    // Keep real Group/GroupHeader/Select/Switch/etc. from actual module
  };
});

import { PlanPagoView } from "../PlanPagoView";

// ── Fixtures ──────────────────────────────────────────────────────────────────

function makeFullPricing(over: Partial<ThreeChargePricing> = {}): ThreeChargePricing {
  return {
    price: 4500,
    price_mode: "fijo",
    price_publishable: true,
    currency: "MXN",
    reservation: { enabled: false, amount: null, kind: "monto" },
    advance: { enabled: true, amount: 30, kind: "porcentaje" },
    financing: { offered: true, installments: 6, interest_kind: "sin_interes", finance_partner: null },
    ...over,
  };
}

function makeServiceDetail(over: Partial<ServiceDetail> = {}): ServiceDetail {
  return {
    offer_id: "offer-123",
    public_name: "Implante dental",
    category: "Odontología",
    modality: "sesiones",
    status: "active",
    value_level: "transformacion",
    canonical_service_ref: null,
    price: 4500,
    currency: "MXN",
    is_active: true,
    sales_brief: null,
    specialists: [],
    cases: [],
    testimonials: [],
    pricing: null,
    ...over,
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("PlanPagoView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // (a) Loading skeleton
  it("renders loading skeleton when servicio is undefined", () => {
    mockUseServicioDetail.mockReturnValue({ data: undefined });
    const { container } = render(<PlanPagoView offerId="offer-123" />);
    const pulses = container.querySelectorAll(".animate-pulse");
    expect(pulses.length).toBeGreaterThanOrEqual(3);
  });

  // (b) Enabled fields — not disabled stubs
  it("renders enabled form fields (no Sub-phase A stubs)", () => {
    mockUseServicioDetail.mockReturnValue({ data: makeServiceDetail() });
    render(<PlanPagoView offerId="offer-123" />);

    // price field should be present and NOT disabled
    const priceInputs = screen.getAllByRole("spinbutton");
    // At least the price field exists (installments may also be spinbutton)
    expect(priceInputs.length).toBeGreaterThanOrEqual(1);

    // "Próximamente" and disabled placeholders from old stub must NOT appear
    expect(screen.queryByText("Próximamente")).toBeNull();
    expect(screen.queryByText("(Disponible próximamente — Sub-phase B)")).toBeNull();
  });

  // (b) All 4 group headers
  it("renders all 4 payment section headers", () => {
    mockUseServicioDetail.mockReturnValue({ data: makeServiceDetail() });
    render(<PlanPagoView offerId="offer-123" />);
    expect(screen.getByText("Precio del tratamiento")).toBeInTheDocument();
    // Reserva header (use getAllByText — whatFor chip may also contain the text)
    expect(screen.getAllByText(/Reserva de la cita/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Anticipo para iniciar/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Financiamiento del saldo/i).length).toBeGreaterThanOrEqual(1);
  });

  // (c) Hydration from servicio.pricing
  it("hydrates form from servicio.pricing when present", () => {
    const pricing = makeFullPricing({ price: 4500, advance: { enabled: true, amount: 30, kind: "porcentaje" } });
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ price: 4500, pricing }),
    });
    render(<PlanPagoView offerId="offer-123" />);
    // The price spinbutton should show 4500
    const spinbuttons = screen.getAllByRole("spinbutton") as HTMLInputElement[];
    const priceInput = spinbuttons[0]; // price is first
    expect(priceInput.value).toBe("4500");
  });

  // (c) G2-F14b regression: the BE serializes Decimal money as JSON STRINGS
  // ("4500"). NumberWithUnit renders empty for non-finite values, so without
  // coercion the amount inputs are blank on reload. Use string amounts (the real
  // wire shape) — the prior fixtures used numbers and never caught this.
  it("hydrates Decimal amounts serialized as strings (BE wire reality) — G2-F14b", () => {
    const pricing = makeFullPricing({
      price: "4500" as unknown as number,
      reservation: { enabled: true, amount: "250" as unknown as number, kind: "monto" },
      advance: { enabled: true, amount: "30" as unknown as number, kind: "porcentaje" },
    });
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ price: "4500" as unknown as number, pricing }),
    });
    render(<PlanPagoView offerId="offer-123" />);
    // None of the amount inputs may be empty (string → number coercion).
    expect((screen.getByLabelText("Precio del tratamiento") as HTMLInputElement).value).toBe("4500");
    expect((screen.getByLabelText("Monto de la reserva") as HTMLInputElement).value).toBe("250");
    expect((screen.getByLabelText("Monto del anticipo") as HTMLInputElement).value).toBe("30");
  });

  // (d) Seeded defaults when pricing is null
  it("seeds sensible defaults when servicio.pricing is null", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ price: 3000, pricing: null }),
    });
    render(<PlanPagoView offerId="offer-123" />);
    // Price should come from servicio.price
    const spinbuttons = screen.getAllByRole("spinbutton") as HTMLInputElement[];
    expect(spinbuttons[0].value).toBe("3000");
    // Switches for enabled/offered should default to off
    // The switches render but shouldn't cause a crash
    expect(screen.getByLabelText("Pide reserva para agendar")).toBeDefined();
    expect(screen.getByLabelText("Requiere anticipo para iniciar")).toBeDefined();
    expect(screen.getByLabelText("Ofrece pago en cuotas")).toBeDefined();
  });

  // (d) G2-F14 regression: servicio loads AFTER an initial undefined render
  // (the reload scenario). Without defaultValues seeding the full shape, the
  // first post-load render reads form.watch("reservation") before the `values`
  // effect syncs → undefined → "Cannot read properties of undefined (reading
  // 'enabled')" crash at runtime. defaultValues makes the nested objects exist.
  it("does not crash when servicio loads after an initial undefined render (G2-F14)", () => {
    mockUseServicioDetail.mockReturnValue({ data: undefined });
    const { rerender } = render(<PlanPagoView offerId="offer-123" />);
    // servicio resolves with pricing null (older service / reload)
    mockUseServicioDetail.mockReturnValue({ data: makeServiceDetail({ pricing: null }) });
    expect(() => rerender(<PlanPagoView offerId="offer-123" />)).not.toThrow();
    expect(screen.getByText("Precio del tratamiento")).toBeInTheDocument();
    // calculated read-only fields render the "—" placeholder, not a crash
    expect((screen.getByLabelText("Equivale a (calculado)") as HTMLInputElement).value).toBe("—");
  });

  // (e) Calculated field: advance_equiv
  it("shows advance_equiv calculation in read-only field (30% of 4500 = 1350)", () => {
    const pricing = makeFullPricing({
      price: 4500,
      advance: { enabled: true, amount: 30, kind: "porcentaje" },
    });
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ price: 4500, pricing }),
    });
    render(<PlanPagoView offerId="offer-123" />);
    // advance_equiv = 4500 * 30/100 = 1350
    const equivInput = screen.getByLabelText("Equivale a (calculado)") as HTMLInputElement;
    // Value contains "1350" (locale formatting may vary in test env)
    expect(equivInput.value).toContain("1350");
    expect(equivInput).toBeDisabled();
  });

  // (e) Calculated field: per_month
  it("shows per_month calculation in read-only field ((4500-0-1350)/6 = 525)", () => {
    const pricing = makeFullPricing({
      price: 4500,
      reservation: { enabled: false, amount: null, kind: "monto" },
      advance: { enabled: true, amount: 30, kind: "porcentaje" },
      financing: { offered: true, installments: 6, interest_kind: "sin_interes", finance_partner: null },
    });
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ price: 4500, pricing }),
    });
    render(<PlanPagoView offerId="offer-123" />);
    // per_month = (4500 - 0 - 1350) / 6 = 525
    const perMonthInput = screen.getByLabelText("Pago mensual calculado") as HTMLInputElement;
    // Value must be numeric and contain 525 (locale formatting may vary)
    expect(perMonthInput.value).toContain("525");
    expect(perMonthInput).toBeDisabled();
  });

  // (f) Patch — dual-sync price (top-level + pricing.price)
  it("schedules dual-sync patch when headline price changes", async () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ price: 4500, pricing: null }),
    });
    render(<PlanPagoView offerId="offer-123" />);
    const spinbuttons = screen.getAllByRole("spinbutton") as HTMLInputElement[];
    const priceInput = spinbuttons[0];
    fireEvent.change(priceInput, { target: { value: "5000" } });

    await waitFor(() => {
      expect(mockSchedule).toHaveBeenCalled();
      const call = mockSchedule.mock.calls[mockSchedule.mock.calls.length - 1][0];
      // Must include top-level price AND pricing.price
      expect(call).toHaveProperty("price", 5000);
      expect(call.pricing?.price).toBe(5000);
    });
  });

  // (f) Patch — non-price field only sends pricing (not top-level price)
  it("does NOT send top-level price when non-price field changes", async () => {
    const pricing = makeFullPricing({ price: 4500 });
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ price: 4500, pricing }),
    });
    render(<PlanPagoView offerId="offer-123" />);

    // Toggle reservation switch
    const reservaSwitch = screen.getByLabelText("Pide reserva para agendar");
    fireEvent.click(reservaSwitch);

    await waitFor(() => {
      expect(mockSchedule).toHaveBeenCalled();
      const call = mockSchedule.mock.calls[mockSchedule.mock.calls.length - 1][0];
      // top-level `price` key should NOT appear (only pricing patch)
      expect(call).not.toHaveProperty("price");
      expect(call).toHaveProperty("pricing");
    });
  });

  // (f) Patch always contains full pricing object
  it("patch always contains price_mode and price_publishable (BE required fields)", async () => {
    const pricing = makeFullPricing();
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ pricing }),
    });
    render(<PlanPagoView offerId="offer-123" />);

    const reservaSwitch = screen.getByLabelText("Pide reserva para agendar");
    fireEvent.click(reservaSwitch);

    await waitFor(() => {
      const call = mockSchedule.mock.calls[mockSchedule.mock.calls.length - 1][0];
      expect(call.pricing).toBeDefined();
      expect(call.pricing.price_mode).toBeDefined();
      expect(call.pricing.price_publishable).toBeDefined();
    });
  });

  // (g) FloatingAutosaveIndicator: exactly one
  it("renders FloatingAutosaveIndicator exactly once (canon §2.6)", () => {
    mockUseServicioDetail.mockReturnValue({ data: makeServiceDetail() });
    render(<PlanPagoView offerId="offer-123" />);
    const indicators = screen.getAllByTestId("floating-autosave");
    expect(indicators).toHaveLength(1);
  });

  // (h) Currency fallback
  it("falls back to locale.currency when servicio.currency is null", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ currency: undefined }),
    });
    render(<PlanPagoView offerId="offer-123" />);
    // MXN from mocked useTenantLocale appears in the currency badge
    expect(screen.getAllByText("MXN").length).toBeGreaterThanOrEqual(1);
  });

  it("shows COP when servicio.currency is COP", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ currency: "COP" }),
    });
    render(<PlanPagoView offerId="offer-123" />);
    expect(screen.getAllByText("COP").length).toBeGreaterThanOrEqual(1);
  });
});
