// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-8
/**
 * EspecialistasView.test.tsx — Leaf 3 unit tests.
 *
 * G2-F13 regression coverage (bugfix — specialist name not displayed):
 *   (a) With display_name + specialty → renders name + specialty (NOT UUID)
 *   (b) Without display_name (null) → renders "Especialista" + id short (NOT UUID crudo)
 *
 * Existing coverage:
 *   - Loading skeleton while data loads
 *   - Empty specialists state: dashed placeholder + link to lisa/doctores (RN-9)
 *   - "Vincular especialista" button opens the EspecialistaLinkPicker
 *   - "Desvincular" calls useUnlinkSpecialist
 *   - "Ver detalle" link points to /lisa/staff/{doctor_id}
 *
 * spec_anchor: 01-spec.md §Workspace Pestaña 3 · 03-arch-fe.md §8 Tests
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ServiceDetail } from "../../../../types/servicios.types";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn(), isLoaded: true, isSignedIn: true }),
  useUser: () => ({ user: { id: "user-1" }, isLoaded: true }),
}));

vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: () => "tenant-abc",
}));

vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: () => "clinic-xyz",
}));

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

const mockUseServicioDetail = vi.fn();
const mockUnlink = vi.fn();

vi.mock("../../../../api/servicios", () => ({
  useServicioDetail: () => mockUseServicioDetail(),
  useUnlinkSpecialist: () => ({ mutate: mockUnlink, isPending: false }),
  useLinkSpecialist: () => ({ mutate: vi.fn(), isPending: false }),
}));

// Stub EspecialistaLinkPicker to avoid its own hook dependencies (staff roster etc.)
vi.mock("../../EspecialistaLinkPicker", () => ({
  EspecialistaLinkPicker: ({
    offerId,
    onClose,
  }: {
    offerId: string;
    linkedDoctorIds: string[];
    onClose: () => void;
  }) => (
    <div data-testid="especialista-link-picker" data-offer-id={offerId}>
      <input placeholder="Buscar por nombre o especialidad…" />
      <button onClick={onClose}>Cerrar picker</button>
    </div>
  ),
}));

import { EspecialistasView } from "../EspecialistasView";

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

describe("EspecialistasView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading skeleton when servicio is undefined", () => {
    mockUseServicioDetail.mockReturnValue({ data: undefined });
    const { container } = render(<EspecialistasView offerId="offer-123" />);
    const pulses = container.querySelectorAll(".animate-pulse");
    expect(pulses.length).toBeGreaterThanOrEqual(3);
  });

  it("renders empty state with warning and link to lisa/staff when no specialists (RN-9)", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ specialists: [] }),
    });
    render(<EspecialistasView offerId="offer-123" />);
    expect(screen.getByText("No hay especialistas vinculados todavía.")).toBeInTheDocument();
    expect(
      screen.getByText(/Vincúlalos para que Adrián pueda asignar el especialista correcto/)
    ).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /Agrega especialistas en Lisa → Especialistas/ });
    expect(link).toHaveAttribute("href", "/tenant-abc/lisa/staff");
  });

  // ── G2-F13 regression: display_name + specialty ─────────────────────────────────

  it("[G2-F13] renders display_name and specialty when BE enriches the DTO", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({
        specialists: [
          {
            id: "link-1",
            offer_id: "offer-123",
            doctor_id: "doc-uuid-1",
            display_name: "Dra. María López",
            specialty: "Odontología estética",
          },
        ],
      }),
    });
    render(<EspecialistasView offerId="offer-123" />);
    // Name rendered — NOT the UUID
    expect(screen.getByText("Dra. María López")).toBeInTheDocument();
    // Specialty rendered as secondary line
    expect(screen.getByText("Odontología estética")).toBeInTheDocument();
    // UUID must NOT appear as the primary label
    expect(screen.queryByText("Doctor ID: doc-uuid-1")).not.toBeInTheDocument();
    expect(screen.queryByText("doc-uuid-1")).not.toBeInTheDocument();
  });

  it("[G2-F13] renders initials from display_name in AvatarFallback", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({
        specialists: [
          {
            id: "link-1",
            offer_id: "offer-123",
            doctor_id: "doc-uuid-1",
            display_name: "Carlos Pérez",
            specialty: "Nutrición clínica",
          },
        ],
      }),
    });
    const { container } = render(<EspecialistasView offerId="offer-123" />);
    // AvatarFallback should display "CP" (first letters of both words)
    const fallback = container.querySelector(".text-xs");
    expect(fallback?.textContent).toBe("CP");
  });

  it("[G2-F13] fallback to 'Especialista' + short id when display_name is null", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({
        specialists: [
          {
            id: "link-1",
            offer_id: "offer-123",
            doctor_id: "doc-uuid-ABCDEFGH-extra",
            display_name: null,
            specialty: null,
          },
        ],
      }),
    });
    render(<EspecialistasView offerId="offer-123" />);
    // Graceful fallback: "Especialista" as name
    expect(screen.getByText("Especialista")).toBeInTheDocument();
    // Short id (first 8 chars) shown as secondary line — NOT full UUID
    expect(screen.getByText("doc-uuid")).toBeInTheDocument();
    // Full UUID should NOT appear
    expect(screen.queryByText("doc-uuid-ABCDEFGH-extra")).not.toBeInTheDocument();
    // "Doctor ID: ..." raw pattern must be gone
    expect(screen.queryByText(/Doctor ID:/)).not.toBeInTheDocument();
  });

  it("[G2-F13] multiple specialists: each renders its own name or fallback", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({
        specialists: [
          {
            id: "link-1",
            offer_id: "offer-123",
            doctor_id: "doc-uuid-1",
            display_name: "Ana Torres",
            specialty: "Dermatología",
          },
          {
            id: "link-2",
            offer_id: "offer-123",
            doctor_id: "doc-uuid-2",
            display_name: null,
            specialty: null,
          },
        ],
      }),
    });
    render(<EspecialistasView offerId="offer-123" />);
    expect(screen.getByText("Ana Torres")).toBeInTheDocument();
    expect(screen.getByText("Dermatología")).toBeInTheDocument();
    // Second specialist has fallback
    expect(screen.getByText("Especialista")).toBeInTheDocument();
    expect(screen.getByText("doc-uuid")).toBeInTheDocument();
    const unlinkButtons = screen.getAllByRole("button", { name: "Desvincular" });
    expect(unlinkButtons).toHaveLength(2);
  });

  // ── Existing interaction tests (kept, adapted) ────────────────────────────────

  it("calls useUnlinkSpecialist mutate with doctor_id when Desvincular clicked", async () => {
    const user = userEvent.setup();
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({
        specialists: [
          {
            id: "link-1",
            offer_id: "offer-123",
            doctor_id: "doc-uuid-1",
            display_name: "Ana Torres",
            specialty: "Dermatología",
          },
        ],
      }),
    });
    render(<EspecialistasView offerId="offer-123" />);
    await user.click(screen.getByRole("button", { name: "Desvincular" }));
    expect(mockUnlink).toHaveBeenCalledWith("doc-uuid-1");
  });

  it("shows EspecialistaLinkPicker when 'Vincular especialista' clicked", async () => {
    const user = userEvent.setup();
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({ specialists: [] }),
    });
    render(<EspecialistasView offerId="offer-123" />);
    await user.click(screen.getByRole("button", { name: "Vincular especialista" }));
    // Picker renders with its search input
    expect(screen.getByPlaceholderText("Buscar por nombre o especialidad…")).toBeInTheDocument();
  });

  it("includes 'Ver detalle' link for each specialist pointing to doctor workspace", () => {
    mockUseServicioDetail.mockReturnValue({
      data: makeServiceDetail({
        specialists: [
          {
            id: "link-1",
            offer_id: "offer-123",
            doctor_id: "doc-uuid-1",
            display_name: "Ana Torres",
            specialty: "Dermatología",
          },
        ],
      }),
    });
    render(<EspecialistasView offerId="offer-123" />);
    const detailLink = screen.getByRole("link", { name: "Ver detalle ↗" });
    expect(detailLink).toHaveAttribute("href", "/tenant-abc/lisa/staff/doc-uuid-1");
  });
});
