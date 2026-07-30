// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * EscaleraView.test.tsx — Component unit tests (TDD).
 *
 * Covers:
 *   - Groups items into their 5 fixed rungs by value_level (RN-2)
 *   - Items with no value_level fall back to the transformacion spine
 *   - estandar items (canonical_service_ref present) render LOCKED (data-locked)
 *   - empty rungs show the biblioteca hint
 *   - loading / error states render
 *
 * Mocks: next/navigation, ../../api/servicios (useEscalera + useMoveRung).
 *
 * downstream-regression-na: brand-local vitalia FE tests; no cross-brand consumers
 * spec_anchor: 06-tickets.yaml T-6 + 01-spec.md AC-3/RN-2/RN-30
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ServiceListItem } from "../../../types/servicios.types";

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({ push: vi.fn() })),
}));

const mockUseEscalera = vi.fn();
vi.mock("../../../api/servicios", () => ({
  useEscalera: () => mockUseEscalera(),
  useMoveRung: () => ({ mutate: vi.fn() }),
}));

import { EscaleraView } from "../EscaleraView";

function makeItem(over: Partial<ServiceListItem> = {}): ServiceListItem {
  return {
    offer_id: "off-x",
    public_name: "Servicio X",
    category: "Odontología",
    modality: "unica",
    status: "active",
    value_level: "transformacion",
    canonical_service_ref: null,
    price: 500,
    currency: "PEN",
    is_active: true,
    ...over,
  };
}

function mockData(items: ServiceListItem[]) {
  mockUseEscalera.mockReturnValue({
    data: { items, next_cursor: null },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  });
}

describe("EscaleraView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the loading skeleton while fetching", () => {
    mockUseEscalera.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    });
    render(<EscaleraView tenantId="t-1" />);
    expect(screen.getByTestId("escalera-skeleton")).toBeInTheDocument();
  });

  it("renders an error state with retry on failure", () => {
    mockUseEscalera.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: vi.fn(),
    });
    render(<EscaleraView tenantId="t-1" />);
    expect(screen.getByTestId("escalera-error")).toBeInTheDocument();
  });

  it("renders the 5 fixed rung columns", () => {
    mockData([]);
    render(<EscaleraView tenantId="t-1" />);
    for (const id of [
      "lead_magnet",
      "activacion",
      "transformacion",
      "maximizacion",
      "corporativo",
    ]) {
      expect(screen.getByTestId(`rung-col-${id}`)).toBeInTheDocument();
    }
  });

  it("groups each item into the rung matching its value_level (RN-2)", () => {
    mockData([
      makeItem({ offer_id: "gancho", value_level: "lead_magnet" }),
      makeItem({ offer_id: "premium", value_level: "maximizacion" }),
    ]);
    render(<EscaleraView tenantId="t-1" />);
    const lead = screen.getByTestId("rung-col-lead_magnet");
    const max = screen.getByTestId("rung-col-maximizacion");
    expect(lead).toContainElement(screen.getByTestId("lad-card-gancho"));
    expect(max).toContainElement(screen.getByTestId("lad-card-premium"));
  });

  it("falls back to the transformacion spine when value_level is missing", () => {
    mockData([makeItem({ offer_id: "huerfano", value_level: undefined })]);
    render(<EscaleraView tenantId="t-1" />);
    expect(
      screen.getByTestId("rung-col-transformacion"),
    ).toContainElement(screen.getByTestId("lad-card-huerfano"));
  });

  it("renders estandar items as LOCKED (data-locked=true · RN-30)", () => {
    mockData([
      makeItem({
        offer_id: "std",
        value_level: "activacion",
        canonical_service_ref: "canon-limpieza",
      }),
    ]);
    render(<EscaleraView tenantId="t-1" />);
    expect(screen.getByTestId("lad-card-std")).toHaveAttribute(
      "data-locked",
      "true",
    );
  });

  it("shows the biblioteca hint inside an empty rung", () => {
    mockData([]);
    render(<EscaleraView tenantId="t-1" />);
    expect(
      screen.getByTestId("rung-empty-hint-lead_magnet"),
    ).toBeInTheDocument();
  });
});
