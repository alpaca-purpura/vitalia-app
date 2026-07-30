// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-8
/**
 * PruebaSocialView.test.tsx — Leaf 5 unit tests.
 *
 * Covers:
 *   - Loading skeleton while data loads
 *   - Testimonial list renders (author, rating stars, source badge)
 *   - Empty testimonial state renders dashed border placeholder
 *   - Testimonial add form appears when "+ Agregar testimonio" clicked
 *   - Form validates: author required, rating 1-5, text min 10 chars
 *   - Cases (before/after) PHI section shows "Próximamente" badge (read-only Sub-phase A)
 *   - consent_signed badge shows on case item
 *
 * spec_anchor: 01-spec.md §Workspace Pestaña 5 · 03-arch-fe.md §8 Tests
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ServiceDetail } from "../../../../types/servicios.types";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn(), isLoaded: true, isSignedIn: true }),
}));

vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: () => "tenant-abc",
}));

const mockUseServicioDetail = vi.fn();
const mockAddTestimonial = vi.fn();
vi.mock("../../../../api/servicios", () => ({
  useServicioDetail: () => mockUseServicioDetail(),
  useAddTestimonial: () => ({ mutate: mockAddTestimonial, isPending: false }),
}));

import { PruebaSocialView } from "../PruebaSocialView";

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

describe("PruebaSocialView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading skeleton when servicio is undefined", () => {
    mockUseServicioDetail.mockReturnValue({ data: undefined });
    const { container } = render(<PruebaSocialView offerId="offer-123" />);
    const pulses = container.querySelectorAll(".animate-pulse");
    expect(pulses.length).toBeGreaterThanOrEqual(3);
  });

  it("renders testimonial list with author, rating stars, and source badge", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({
        testimonials: [
          {
            id: "t1",
            offer_id: "offer-123",
            author: "Ana García",
            rating: 5,
            text: "Excelente tratamiento, muy recomendado.",
            source: "Google",
          },
        ],
      }),
    });
    render(<PruebaSocialView offerId="offer-123" />);
    expect(screen.getByText("Ana García")).toBeInTheDocument();
    // 5 filled stars
    expect(screen.getByText("★★★★★")).toBeInTheDocument();
    expect(screen.getByText("Excelente tratamiento, muy recomendado.")).toBeInTheDocument();
    expect(screen.getByText("Google")).toBeInTheDocument();
  });

  it("renders star rating correctly for partial ratings", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({
        testimonials: [
          { id: "t1", offer_id: "offer-123", author: "Luis", rating: 3, text: "Buen servicio.", source: "Directo" },
        ],
      }),
    });
    render(<PruebaSocialView offerId="offer-123" />);
    // 3 filled + 2 empty
    expect(screen.getByText("★★★☆☆")).toBeInTheDocument();
  });

  it("renders empty testimonials state with dashed placeholder", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ testimonials: [] }),
    });
    render(<PruebaSocialView offerId="offer-123" />);
    expect(screen.getByText("No hay testimonios todavía.")).toBeInTheDocument();
  });

  it("shows the add testimonial form after clicking '+ Agregar testimonio'", async () => {
    const user = userEvent.setup();
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ testimonials: [] }),
    });
    render(<PruebaSocialView offerId="offer-123" />);
    const addBtn = screen.getByRole("button", { name: "+ Agregar testimonio" });
    await user.click(addBtn);
    expect(screen.getByText("Agregar testimonio")).toBeInTheDocument();
    expect(screen.getByLabelText("Nombre del paciente")).toBeInTheDocument();
  });

  it("shows validation error when submitting form with empty author", async () => {
    const user = userEvent.setup();
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ testimonials: [] }),
    });
    render(<PruebaSocialView offerId="offer-123" />);
    await user.click(screen.getByRole("button", { name: "+ Agregar testimonio" }));
    // Submit with empty fields
    const submitBtn = screen.getByRole("button", { name: "Agregar" });
    await user.click(submitBtn);
    await waitFor(() => {
      expect(screen.getByText("El nombre es requerido")).toBeInTheDocument();
    });
  });

  it("shows validation error when text is too short", async () => {
    const user = userEvent.setup();
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ testimonials: [] }),
    });
    render(<PruebaSocialView offerId="offer-123" />);
    await user.click(screen.getByRole("button", { name: "+ Agregar testimonio" }));
    await user.type(screen.getByLabelText("Nombre del paciente"), "María");
    await user.type(screen.getByLabelText("Texto del testimonio"), "Corto");
    await user.click(screen.getByRole("button", { name: "Agregar" }));
    await waitFor(() => {
      expect(screen.getByText("El testimonio debe tener al menos 10 caracteres")).toBeInTheDocument();
    });
  });

  it("renders Cases antes/después section with 'Próximamente' badge (PHI read-only — Sub-phase A)", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ cases: [] }),
    });
    render(<PruebaSocialView offerId="offer-123" />);
    expect(screen.getByText("Casos antes/después")).toBeInTheDocument();
    expect(screen.getByText("Próximamente")).toBeInTheDocument();
    expect(screen.getByText(/Los casos PHI.*estarán disponibles/)).toBeInTheDocument();
  });

  it("renders case items (read-only) with consent_signed badge when present", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({
        cases: [
          {
            id: "case-1",
            offer_id: "off-a",
            before_asset_url: "https://cdn.example.com/before.jpg",
            after_asset_url: "https://cdn.example.com/after.jpg",
            consent_signed: true,
            consent_ref: "consent-1",
          },
        ],
      }),
    });
    render(<PruebaSocialView offerId="offer-123" />);
    expect(screen.getByText("before.jpg", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("Consentimiento firmado")).toBeInTheDocument();
  });
});
