// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-8 + T-R3
/**
 * ResumenView.test.tsx — Leaf 1 unit tests.
 *
 * Covers (T-8):
 *   - Loading skeleton renders when servicio not loaded yet
 *   - Modality discriminated reveal (ModalidadPicker renders with current value)
 *   - Estandar flag → RungPicker renders locked (RN-30/RN-31)
 *   - Personalizado → RungPicker is NOT locked
 *   - Skeleton shows pulsing placeholders while data loads
 *
 * T-R3 additions (03-arch-reconcile-delta.md §C.2):
 *   - CollapsibleSection renders (6 section titles present)
 *   - Rich field hydration: description_long, includes, procedure_steps, risks bound to servicio
 *   - Autosave schedule called on description_long change
 *   - Modality conditionals: session_interval shown when modality=sesiones
 *   - Modality conditionals: recurrence_interval shown when modality=recurrente
 *   - VariantsRepeater receives servicio.variants (not hardcoded [])
 *   - Currency not hardcoded as USD (no "USD" passed when currency is null)
 *
 * spec_anchor: 01-spec.md §Workspace Pestaña 1 · 03-arch-fe.md §8 Tests · 03-arch-reconcile-delta.md §C.2
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ServiceDetail } from "../../../../types/servicios.types";

// ── Mock Clerk (always required in FE vitalia tests) ────────────────────────
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn(), isLoaded: true, isSignedIn: true }),
}));

vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: () => "tenant-abc",
}));

vi.mock("@/hooks/useTenantLocale", () => ({
  useTenantLocale: () => ({ currency: "PEN", locale: "es-PE" }),
}));

// ── Mock use-autosave (canonical hook — capture schedule for T-R3 assertions) ──
const mockSchedule = vi.fn();
vi.mock("@/hooks/use-autosave", () => ({
  useAutosave: () => ({ schedule: mockSchedule, status: "idle", flush: vi.fn() }),
}));

// ── Cycling autosave status factory (for G2-F11 regression — NOT frozen) ────
// Returns a hook impl that cycles status idle→saving→saved on each schedule call,
// mimicking real re-renders that expose the value={servicio.X} bug.
function makeCyclingAutosave() {
  let _status: "idle" | "saving" | "saved" = "idle";
  const schedule = vi.fn((payload: unknown) => {
    void payload; // fire-and-forget, like real hook
    _status = "saving";
    // Sync: immediately flip to saved so React re-renders in the same act()
    _status = "saved";
  });
  return {
    useAutosave: () => ({ schedule, status: _status, flush: vi.fn() }),
    getSchedule: () => schedule,
  };
}

// ── Mock api/servicios hooks ──────────────────────────────────────────────
const mockUseServicioDetail = vi.fn();
vi.mock("../../../../api/servicios", () => ({
  useServicioDetail: () => mockUseServicioDetail(),
  usePatchField: () => ({ mutateAsync: vi.fn() }),
}));

// ── Mock @luana/ui-kit selectively ────────────────────────────────────────
vi.mock("@luana/ui-kit", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@luana/ui-kit")>();
  return {
    ...actual,
    FloatingAutosaveIndicator: ({ status }: { status: string }) => (
      <div data-testid="floating-autosave" data-status={status} />
    ),
    // RichSelect uses FormControl internally (requires RHF context) — stub for unit tests
    RichSelect: ({ value, placeholder }: { value?: string; placeholder?: string }) => (
      <div data-testid="rich-select" data-value={value ?? ""}>{placeholder}</div>
    ),
    // CollapsibleSection: strip Radix accordion so content always visible in unit tests.
    // Real accordion hides content via CSS animation (height:0) when closed — JSDOM
    // doesn't run CSS so getByDisplayValue can't find values inside closed sections.
    CollapsibleSection: ({
      title,
      children,
      summary,
    }: {
      title: string;
      children: React.ReactNode;
      summary?: React.ReactNode;
      defaultOpen?: boolean;
      accentVar?: string;
    }) => (
      <div data-testid={`collapsible-section-${title.toLowerCase().replace(/\s+/g, "-")}`}>
        <div data-role="section-title">{title}</div>
        {summary != null && <div data-role="section-summary">{summary}</div>}
        <div data-role="section-content">{children}</div>
      </div>
    ),
  };
});

// VariantsRepeater: stub captures props so T-R3 can assert hydration.
// Path must match how ResumenView imports it (from leaves/ → ../VariantsRepeater).
// vi.mock resolves relative to the module being mocked, not the test file.
vi.mock("../../VariantsRepeater", () => ({
  VariantsRepeater: ({ value, currency }: { value: unknown[]; currency?: string }) => (
    <div
      data-testid="variants-repeater"
      data-value-length={String(value.length)}
      data-currency={currency ?? ""}
    />
  ),
}));

import { ResumenView } from "../ResumenView";

function makeServiceDetail(over: Partial<ServiceDetail> = {}): ServiceDetail {
  return {
    offer_id: "offer-123",
    public_name: "Blanqueamiento dental",
    category: "Odontología",
    modality: "unica",
    status: "active",
    value_level: "transformacion",
    canonical_service_ref: null,
    price: 500,
    currency: "PEN",
    is_active: true,
    // Rich fields (T-R3 — hydrated from BE post T-R1)
    description_long: "Tratamiento láser de última generación",
    includes: "Consulta previa, sesión láser y control a 2 semanas",
    excludes: null,
    warranty: null,
    procedure_steps: "1. Evaluación. 2. Aplicación del gel activador. 3. Irradiación 20 min.",
    anesthesia_pain: null,
    prep: null,
    aftercare: "Evitar alimentos con colorantes 48h",
    downtime: null,
    expected_result: "Hasta 8 tonos más claro",
    result_timing: null,
    result_lifespan: null,
    realistic_expectations: null,
    risks: "Sensibilidad temporal (24-48h)",
    red_flags: null,
    initial_appt_duration_minutes: 60,
    initial_appt_type: null,
    variants: [{ id: "v1", name: "Composite", price: 2500, note: undefined }],
    session_interval: null,
    recurrence_interval: null,
    sales_brief: null,
    specialists: [],
    cases: [],
    testimonials: [],
    ...over,
  };
}

describe("ResumenView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading skeleton when servicio is undefined", () => {
    mockUseServicioDetail.mockReturnValue({ data: undefined });
    const { container } = render(<ResumenView offerId="offer-123" />);
    // 4 animate-pulse placeholders
    const pulses = container.querySelectorAll(".animate-pulse");
    expect(pulses.length).toBeGreaterThanOrEqual(4);
  });

  it("renders the form groups when servicio is loaded", () => {
    mockUseServicioDetail.mockReturnValue({ data: makeServiceDetail() });
    render(<ResumenView offerId="offer-123" />);
    // Group headers from the 6 groups
    expect(screen.getByText("Identidad")).toBeInTheDocument();
    expect(screen.getByText("Qué es")).toBeInTheDocument();
    expect(screen.getByText("El procedimiento")).toBeInTheDocument();
    expect(screen.getByText("Resultados")).toBeInTheDocument();
    expect(screen.getByText("Riesgos")).toBeInTheDocument();
    expect(screen.getByText("Modalidad y agenda")).toBeInTheDocument();
  });

  it("renders ModalidadPicker with the servicio modality value (discriminated reveal)", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ modality: "sesiones" }),
    });
    render(<ResumenView offerId="offer-123" />);
    // ModalidadPicker renders 3 radio-like buttons; check "Por sesiones" label
    expect(screen.getByText("Por sesiones")).toBeInTheDocument();
    // The sesiones button should be selected (data-sel=true or aria-checked=true)
    // ModalidadPicker data-testid uses "mod-sesiones"
    const sesionesBtn = screen.getByTestId("mod-sesiones");
    expect(sesionesBtn).toHaveAttribute("aria-checked", "true");
  });

  it("renders RungPicker as LOCKED when servicio is estandar (canonical_service_ref set — RN-30)", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ canonical_service_ref: "blanqueamiento-laser" }),
    });
    render(<ResumenView offerId="offer-123" />);
    // RungPicker buttons should all be disabled when locked
    const rungTransformacion = screen.getByTestId("rung-TRANSFORMACION");
    expect(rungTransformacion).toBeDisabled();
  });

  it("renders RungPicker as interactive (NOT locked) when servicio is personalizado", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ canonical_service_ref: null }),
    });
    render(<ResumenView offerId="offer-123" />);
    const rungTransformacion = screen.getByTestId("rung-TRANSFORMACION");
    expect(rungTransformacion).not.toBeDisabled();
  });

  it("maps lowercase value_level to uppercase for RungPicker (upstream bridge)", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ value_level: "lead_magnet" }),
    });
    render(<ResumenView offerId="offer-123" />);
    // RungPicker uses LEAD_MAGNET (uppercase) as value
    const rungLeadMagnet = screen.getByTestId("rung-LEAD_MAGNET");
    expect(rungLeadMagnet).toHaveAttribute("data-sel", "true");
  });

  it("renders category field disabled when servicio is estandar (inherited from standard)", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ canonical_service_ref: "blanqueamiento-laser", category: "Odontología" }),
    });
    render(<ResumenView offerId="offer-123" />);
    const categoryInput = screen.getByPlaceholderText("Ej. Odontología estética");
    expect(categoryInput).toBeDisabled();
    // Shows inherited hint
    expect(screen.getByText("(heredada del estándar)")).toBeInTheDocument();
  });

  it("renders FloatingAutosaveIndicator once (canon §2.6)", () => {
    mockUseServicioDetail.mockReturnValue({ data: makeServiceDetail() });
    render(<ResumenView offerId="offer-123" />);
    const indicators = screen.getAllByTestId("floating-autosave");
    expect(indicators).toHaveLength(1);
    expect(indicators[0]).toHaveAttribute("data-status", "idle");
  });

  // ── T-R3 tests (03-arch-reconcile-delta.md §C.2) ─────────────────────────

  describe("T-R3 — CollapsibleSection + hydration + autosave + conditionals", () => {
    it("renders all 6 section titles as CollapsibleSection (C.2.1)", () => {
      mockUseServicioDetail.mockReturnValue({ data: makeServiceDetail() });
      render(<ResumenView offerId="offer-123" />);
      // All 6 group titles must be present
      expect(screen.getByText("Identidad")).toBeInTheDocument();
      expect(screen.getByText("Qué es")).toBeInTheDocument();
      expect(screen.getByText("El procedimiento")).toBeInTheDocument();
      expect(screen.getByText("Resultados")).toBeInTheDocument();
      expect(screen.getByText("Riesgos")).toBeInTheDocument();
      expect(screen.getByText("Modalidad y agenda")).toBeInTheDocument();
    });

    it("hydrates description_long value from servicio (C.2.2)", () => {
      mockUseServicioDetail.mockReturnValue({
        data: makeServiceDetail({ description_long: "Blanqueamiento con activación LED" }),
      });
      render(<ResumenView offerId="offer-123" />);
      const textarea = screen.getByDisplayValue("Blanqueamiento con activación LED");
      expect(textarea).toBeInTheDocument();
    });

    it("hydrates includes value from servicio (C.2.2)", () => {
      mockUseServicioDetail.mockReturnValue({
        data: makeServiceDetail({ includes: "Gel activador + protector gingival" }),
      });
      render(<ResumenView offerId="offer-123" />);
      expect(screen.getByDisplayValue("Gel activador + protector gingival")).toBeInTheDocument();
    });

    it("hydrates procedure_steps value from servicio (C.2.2)", () => {
      mockUseServicioDetail.mockReturnValue({
        data: makeServiceDetail({ procedure_steps: "1. Preparación 2. Aplicación" }),
      });
      render(<ResumenView offerId="offer-123" />);
      expect(screen.getByDisplayValue("1. Preparación 2. Aplicación")).toBeInTheDocument();
    });

    it("hydrates risks value from servicio (C.2.2)", () => {
      mockUseServicioDetail.mockReturnValue({
        data: makeServiceDetail({ risks: "Sensibilidad post-tratamiento" }),
      });
      render(<ResumenView offerId="offer-123" />);
      expect(screen.getByDisplayValue("Sensibilidad post-tratamiento")).toBeInTheDocument();
    });

    it("calls schedule with description_long on textarea change (C.2.2 autosave)", async () => {
      const { userEvent } = await import("@testing-library/user-event");
      const ue = userEvent.setup();
      mockUseServicioDetail.mockReturnValue({
        data: makeServiceDetail({ description_long: "" }),
      });
      mockSchedule.mockClear();
      render(<ResumenView offerId="offer-123" />);
      // Find the description_long textarea by placeholder
      const textarea = screen.getByPlaceholderText("Una frase que el paciente entiende al instante");
      await ue.type(textarea, "Test descripción");
      expect(mockSchedule).toHaveBeenCalledWith(
        expect.objectContaining({ description_long: expect.any(String) }),
      );
    });

    it("VariantsRepeater receives servicio.variants not [] (C.2.2)", () => {
      const variants = [{ id: "v1", name: "Porcelana", price: 4500 }];
      mockUseServicioDetail.mockReturnValue({
        data: makeServiceDetail({ variants }),
      });
      render(<ResumenView offerId="offer-123" />);
      const repeater = screen.getByTestId("variants-repeater");
      // data-value-length attribute proves variants passed through
      expect(repeater).toHaveAttribute("data-value-length", "1");
    });

    it("VariantsRepeater does NOT receive 'USD' when currency is PEN (C.2.2 currency canon)", () => {
      mockUseServicioDetail.mockReturnValue({
        data: makeServiceDetail({ currency: "PEN" }),
      });
      render(<ResumenView offerId="offer-123" />);
      const repeater = screen.getByTestId("variants-repeater");
      expect(repeater).toHaveAttribute("data-currency", "PEN");
      expect(repeater).not.toHaveAttribute("data-currency", "USD");
    });

    it("shows session_interval field when modality is sesiones (C.2.3)", () => {
      mockUseServicioDetail.mockReturnValue({
        data: makeServiceDetail({ modality: "sesiones" }),
      });
      render(<ResumenView offerId="offer-123" />);
      // session_interval label visible
      expect(screen.getByText(/intervalo entre sesiones/i)).toBeInTheDocument();
    });

    it("does NOT show session_interval when modality is unica (C.2.3)", () => {
      mockUseServicioDetail.mockReturnValue({
        data: makeServiceDetail({ modality: "unica" }),
      });
      render(<ResumenView offerId="offer-123" />);
      expect(screen.queryByText(/intervalo entre sesiones/i)).not.toBeInTheDocument();
    });

    it("shows recurrence_interval field when modality is recurrente (C.2.3)", () => {
      mockUseServicioDetail.mockReturnValue({
        data: makeServiceDetail({ modality: "recurrente" }),
      });
      render(<ResumenView offerId="offer-123" />);
      expect(screen.getByText(/intervalo de recurrencia/i)).toBeInTheDocument();
    });

    it("does NOT show recurrence_interval when modality is unica (C.2.3)", () => {
      mockUseServicioDetail.mockReturnValue({
        data: makeServiceDetail({ modality: "unica" }),
      });
      render(<ResumenView offerId="offer-123" />);
      expect(screen.queryByText(/intervalo de recurrencia/i)).not.toBeInTheDocument();
    });
  });

  // ── G2-F11 regression: value must come from RHF local state, not servicio ──
  // ADR-vitalia-009 §2.1 invariant: editable inputs MUST NOT bind value={servicio.X}.
  // When status cycles (idle→saving→saved), React re-renders; if value is bound to
  // server data the textarea reverts to the server value on every keystroke (the bug).
  // This test exercises that re-render cycle and asserts the typed value is preserved.
  describe("G2-F11 — autosave re-renders preserve typed value (ADR-009 §2.1)", () => {
    it("description_long textarea keeps typed value after autosave status cycles (RED before fix)", async () => {
      const { userEvent } = await import("@testing-library/user-event");
      const ue = userEvent.setup();

      // Override use-autosave mock for this test to use a cycling status implementation.
      // We need the re-render to happen so we use a ref-based approach: the standard
      // mock above always returns status:"idle" (no re-render). Here we use a controlled
      // React state simulation via a wrapper component.
      const serverValue = "Valor del servidor";
      mockUseServicioDetail.mockReturnValue({
        data: makeServiceDetail({ description_long: serverValue }),
      });

      // We override the mock module factory inline: vi.mock is hoisted so we can't
      // call it inside a describe — instead we spy on the already-mocked module and
      // replace the implementation for this test only.
      const autosaveMod = await import("@/hooks/use-autosave");
      const cycling = makeCyclingAutosave();
      const spy = vi.spyOn(autosaveMod, "useAutosave").mockImplementation(cycling.useAutosave);

      const { rerender } = render(<ResumenView offerId="offer-123" />);

      // Textarea starts with server value (hydration)
      const textarea = screen.getByPlaceholderText(
        "Una frase que el paciente entiende al instante",
      ) as HTMLTextAreaElement;
      expect(textarea.value).toBe(serverValue);

      // Type new text — this calls field.onChange (RHF) + schedule (autosave)
      // The schedule call mutates _status → saved, triggering a re-render via
      // the cycling impl. The re-render will expose the bug if value={servicio.X}.
      await ue.clear(textarea);
      await ue.type(textarea, "Texto escrito por el usuario");

      // Force a re-render (simulates what setStatus("saved") triggers in real hook)
      rerender(<ResumenView offerId="offer-123" />);

      // INVARIANT (ADR-009 §2.1): typed value must survive the re-render.
      // Before fix: value reverts to serverValue (THE BUG).
      // After fix: value is the typed text (RHF local state).
      expect(textarea.value).toBe("Texto escrito por el usuario");

      spy.mockRestore();
    });
  });
});
