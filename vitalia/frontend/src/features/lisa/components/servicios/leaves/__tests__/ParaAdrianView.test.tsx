// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-8
/**
 * ParaAdrianView.test.tsx — Leaf 2 unit tests.
 *
 * Covers:
 *   - Loading skeleton while data loads
 *   - FAQ pairs render from brief.faq
 *   - Objecion pairs render from brief.objections
 *   - Null brief renders empty state (no crash)
 *   - FloatingAutosaveIndicator present once
 *
 * spec_anchor: 01-spec.md §Workspace Pestaña 2 · 03-arch-fe.md §8 Tests
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ServiceDetail } from "../../../../types/servicios.types";

// Hoisted so the use-autosave mock and the assertions share the same spy.
const { mockSchedule } = vi.hoisted(() => ({ mockSchedule: vi.fn() }));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn(), isLoaded: true, isSignedIn: true }),
}));

vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: () => "tenant-abc",
}));

vi.mock("@/hooks/use-autosave", () => ({
  useAutosave: () => ({ schedule: mockSchedule, status: "idle", flush: vi.fn() }),
}));

const mockUseServicioDetail = vi.fn();
vi.mock("../../../../api/servicios", () => ({
  useServicioDetail: () => mockUseServicioDetail(),
  useSalesBriefPatch: () => ({ mutateAsync: vi.fn() }),
}));

vi.mock("@luana/ui-kit", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@luana/ui-kit")>();
  return {
    ...actual,
    FloatingAutosaveIndicator: ({ status }: { status: string }) => (
      <div data-testid="floating-autosave" data-status={status} />
    ),
  };
});

import { ParaAdrianView } from "../ParaAdrianView";

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
    sales_brief: null,
    specialists: [],
    cases: [],
    testimonials: [],
    ...over,
  };
}

describe("ParaAdrianView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading skeleton when servicio is undefined", () => {
    mockUseServicioDetail.mockReturnValue({ data: undefined });
    const { container } = render(<ParaAdrianView offerId="offer-123" />);
    const pulses = container.querySelectorAll(".animate-pulse");
    expect(pulses.length).toBeGreaterThanOrEqual(3);
  });

  it("renders all section groups when servicio is loaded", () => {
    mockUseServicioDetail.mockReturnValue({ data: makeServiceDetail() });
    render(<ParaAdrianView offerId="offer-123" />);
    expect(screen.getByText("Candidatura y seguridad")).toBeInTheDocument();
    expect(screen.getByText("Argumentario")).toBeInTheDocument();
    expect(screen.getByText("Preguntas frecuentes")).toBeInTheDocument();
    expect(screen.getByText("Objeciones y respuestas")).toBeInTheDocument();
    expect(screen.getByText("Para el match")).toBeInTheDocument();
  });

  it("renders null sales_brief without crashing (empty state)", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ sales_brief: null }),
    });
    expect(() => render(<ParaAdrianView offerId="offer-123" />)).not.toThrow();
  });

  it("renders FAQ pairs from brief.faq (inputs with display values)", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({
        sales_brief: {
          id: "brief-1",
          offer_id: "offer-123",
          candidate_ideal: null,
          contraindications: null,
          qualification_questions: null,
          escalation_conditions: null,
          requires_evaluation: false,
          emotional_benefits: null,
          pain_of_not_treating: null,
          differentiators: null,
          promos: null,
          faq: [
            { question: "¿Duele el procedimiento?", answer: "No, es indoloro." },
            { question: "¿Cuántas sesiones necesito?", answer: "Depende del caso." },
          ],
          objections: [],
          keywords: [],
          problems_solved: null,
          language_to_avoid: null,
          updated_at: null,
        },
      }),
    });
    render(<ParaAdrianView offerId="offer-123" />);
    // FaqPairList renders question/answer in <Input value=...> → use getByDisplayValue
    expect(screen.getByDisplayValue("¿Duele el procedimiento?")).toBeInTheDocument();
    expect(screen.getByDisplayValue("No, es indoloro.")).toBeInTheDocument();
    expect(screen.getByDisplayValue("¿Cuántas sesiones necesito?")).toBeInTheDocument();
  });

  it("renders objecion pairs from brief.objections (inputs with display values)", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({
        sales_brief: {
          id: "brief-2",
          offer_id: "offer-123",
          candidate_ideal: null,
          contraindications: null,
          qualification_questions: null,
          escalation_conditions: null,
          requires_evaluation: false,
          emotional_benefits: null,
          pain_of_not_treating: null,
          differentiators: null,
          promos: null,
          faq: [],
          objections: [
            { objection_type: "precio", response: "El costo incluye garantía." },
          ],
          keywords: [],
          problems_solved: null,
          language_to_avoid: null,
          updated_at: null,
        },
      }),
    });
    render(<ParaAdrianView offerId="offer-123" />);
    // ObjecionPairList renders objecion tag in <Input> + response in <Textarea>
    expect(screen.getByDisplayValue("precio")).toBeInTheDocument();
    expect(screen.getByDisplayValue("El costo incluye garantía.")).toBeInTheDocument();
  });

  it("renders FloatingAutosaveIndicator once (canon §2.6)", () => {
    mockUseServicioDetail.mockReturnValue({ data: makeServiceDetail() });
    render(<ParaAdrianView offerId="offer-123" />);
    const indicators = screen.getAllByTestId("floating-autosave");
    expect(indicators).toHaveLength(1);
  });

  // ── G2-F12: empty/partial pairs must NOT autosave ───────────────────────────
  // Domain FaqPair/ObjectionPair require both fields non-empty (a blank FAQ is
  // invalid → BE 500). Adding a row must stay local until it has content.
  function briefWith(over: Record<string, unknown> = {}) {
    return makeServiceDetail({
      sales_brief: {
        id: "brief-empty",
        offer_id: "offer-123",
        candidate_ideal: null,
        contraindications: null,
        qualification_questions: null,
        escalation_conditions: null,
        requires_evaluation: false,
        emotional_benefits: null,
        pain_of_not_treating: null,
        differentiators: null,
        promos: null,
        faq: [],
        objections: [],
        keywords: [],
        problems_solved: null,
        language_to_avoid: null,
        updated_at: null,
        ...over,
      },
    });
  }

  it("adding an empty FAQ pair does NOT trigger a save (G2-F12)", async () => {
    const user = userEvent.setup();
    mockUseServicioDetail.mockReturnValue({ data: briefWith() });
    render(<ParaAdrianView offerId="offer-123" />);

    await user.click(screen.getByRole("button", { name: /agregar pregunta/i }));

    // The empty row is visible (editable) but nothing is persisted.
    expect(mockSchedule).not.toHaveBeenCalled();
  });

  it("saves a FAQ pair only once BOTH fields have content (G2-F12)", async () => {
    const user = userEvent.setup();
    mockUseServicioDetail.mockReturnValue({ data: briefWith() });
    render(<ParaAdrianView offerId="offer-123" />);

    await user.click(screen.getByRole("button", { name: /agregar pregunta/i }));

    // Question only → still incomplete → no save.
    await user.type(screen.getByPlaceholderText("¿Pregunta del paciente?"), "¿Duele?");
    expect(mockSchedule).not.toHaveBeenCalled();

    // Answer too → now complete → save fires, never with an empty pair.
    await user.type(screen.getByPlaceholderText("Respuesta que da Adrián…"), "No");

    expect(mockSchedule).toHaveBeenCalled();
    const sentFaqs = mockSchedule.mock.calls
      .map((c) => c[0]?.faq)
      .filter((f): f is { question: string; answer: string }[] => Array.isArray(f));
    // Last payload carries the complete pair…
    expect(sentFaqs.at(-1)).toEqual([{ question: "¿Duele?", answer: "No" }]);
    // …and no payload ever contained a blank pair.
    for (const faq of sentFaqs) {
      for (const pair of faq) {
        expect(pair.question.trim() === "" && pair.answer.trim() === "").toBe(false);
      }
    }
  });
});
