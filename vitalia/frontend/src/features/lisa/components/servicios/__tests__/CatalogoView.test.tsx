// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * CatalogoView.test.tsx — Component unit tests (TDD).
 *
 * Covers:
 *   - empty state invites the biblioteca (AC-7)
 *   - data renders a grid of ServiceCards + a trailing "+ Nuevo" tile
 *   - client-side rung filter narrows the grid (wire only does q + is_active)
 *   - client-side category filter narrows the grid
 *   - loading / error states render
 *
 * Mocks: next/navigation, ../../api/servicios (useServicios + mutations).
 *
 * downstream-regression-na: brand-local vitalia FE tests; no cross-brand consumers
 * spec_anchor: 06-tickets.yaml T-6 + 01-spec.md AC-1/AC-7
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import type {
  ServiceListItem,
  ServiciosFilters,
} from "../../../types/servicios.types";

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({ push: vi.fn() })),
}));

const mockUseServicios = vi.fn();
vi.mock("../../../api/servicios", () => ({
  useServicios: () => mockUseServicios(),
  useActivateServicio: () => ({ mutate: vi.fn() }),
  useSoftDeleteServicio: () => ({ mutate: vi.fn() }),
}));

import { CatalogoView } from "../CatalogoView";

const NO_FILTERS: ServiciosFilters = {
  search: "",
  category: null,
  rung: null,
  active: "all",
};

function makeItem(over: Partial<ServiceListItem> = {}): ServiceListItem {
  return {
    offer_id: "off-a",
    public_name: "Servicio A",
    category: "Odontología",
    modality: "unica",
    status: "active",
    value_level: "transformacion",
    canonical_service_ref: null,
    price: 800,
    currency: "PEN",
    is_active: true,
    ...over,
  };
}

function mockData(items: ServiceListItem[]) {
  mockUseServicios.mockReturnValue({
    data: { items, next_cursor: null },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  });
}

describe("CatalogoView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the loading skeleton while fetching", () => {
    mockUseServicios.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    });
    render(
      <CatalogoView tenantId="t-1" filters={NO_FILTERS} />,
    );
    expect(screen.getByTestId("catalogo-skeleton")).toBeInTheDocument();
  });

  it("renders the error state with a retry button", () => {
    mockUseServicios.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: vi.fn(),
    });
    render(
      <CatalogoView tenantId="t-1" filters={NO_FILTERS} />,
    );
    expect(screen.getByTestId("catalogo-error")).toBeInTheDocument();
  });

  it("invites the biblioteca when there are no services (AC-7)", () => {
    mockData([]);
    render(
      <CatalogoView tenantId="t-1" filters={NO_FILTERS} />,
    );
    expect(screen.getByTestId("catalogo-empty")).toBeInTheDocument();
    expect(screen.getByTestId("btn-crear-personalizado")).toBeInTheDocument();
  });

  it("renders a grid of cards + a trailing 'Nuevo' tile when there is data", () => {
    mockData([
      makeItem({ offer_id: "a" }),
      makeItem({ offer_id: "b", public_name: "Servicio B" }),
    ]);
    render(
      <CatalogoView tenantId="t-1" filters={NO_FILTERS} />,
    );
    expect(screen.getByTestId("catalogo-grid")).toBeInTheDocument();
    expect(screen.getByTestId("service-card-a")).toBeInTheDocument();
    expect(screen.getByTestId("service-card-b")).toBeInTheDocument();
    expect(screen.getByTestId("catalogo-nuevo-tile")).toBeInTheDocument();
  });

  it("narrows the grid client-side by rung (value_level)", () => {
    mockData([
      makeItem({ offer_id: "lead", value_level: "lead_magnet" }),
      makeItem({ offer_id: "trans", value_level: "transformacion" }),
    ]);
    render(
      <CatalogoView
        tenantId="t-1"
        filters={{ ...NO_FILTERS, rung: "lead_magnet" }}
      />,
    );
    expect(screen.getByTestId("service-card-lead")).toBeInTheDocument();
    expect(screen.queryByTestId("service-card-trans")).not.toBeInTheDocument();
  });

  it("narrows the grid client-side by category (case-insensitive)", () => {
    mockData([
      makeItem({ offer_id: "odo", category: "Odontología" }),
      makeItem({ offer_id: "est", category: "Medicina estética" }),
    ]);
    render(
      <CatalogoView
        tenantId="t-1"
        filters={{ ...NO_FILTERS, category: "odontología" }}
      />,
    );
    expect(screen.getByTestId("service-card-odo")).toBeInTheDocument();
    expect(screen.queryByTestId("service-card-est")).not.toBeInTheDocument();
  });
});
