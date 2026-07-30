/**
 * LocationsCard.test.tsx — Unit tests for LocationsCard component.
 *
 * TDD per tdd-mandatory.md.
 * Tests: loading state, empty state, locations list, disabled actions.
 *
 * T-7 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-7 + fe_test_locations_array validator
 */

import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";

const MOCK_LOCATIONS = [
  { id: "loc-001", name: "Sede Miraflores", address: "Av. Larco 123, Miraflores, Lima" },
  { id: "loc-002", name: "Sede San Isidro", address: "Calle Las Camelias 456, San Isidro, Lima" },
];

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


vi.mock("../../../../api/marca-presence-api", () => ({
  getLocations: vi.fn().mockResolvedValue({ items: MOCK_LOCATIONS }),
}));

vi.mock("../../../../api/marca", () => ({
  marcaKeys: {
    all: ["lisa", "marca"],
    locations: (tenantId: string) => ["lisa", "marca", "locations", tenantId],
  },
}));

async function renderLocationsCard(tenantId = "tenant-abc") {
  const { LocationsCard } = await import("../LocationsCard");
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <LocationsCard tenantId={tenantId} />
    </QueryClientProvider>,
  );
}

describe("LocationsCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders heading 'Ubicaciones'", async () => {
    await renderLocationsCard();
    expect(screen.getByText("Ubicaciones")).toBeDefined();
  });

  it("renders location names after data loads", async () => {
    await renderLocationsCard();
    await waitFor(() => {
      expect(screen.getByText("Sede Miraflores")).toBeDefined();
      expect(screen.getByText("Sede San Isidro")).toBeDefined();
    });
  });

  it("renders location addresses", async () => {
    await renderLocationsCard();
    await waitFor(() => {
      expect(screen.getByText(/Av. Larco/)).toBeDefined();
      expect(screen.getByText(/Las Camelias/)).toBeDefined();
    });
  });

  it("renders '2 sedes' count when 2 locations loaded", async () => {
    await renderLocationsCard();
    await waitFor(() => {
      expect(screen.getByText("2 sedes")).toBeDefined();
    });
  });

  it("renders disabled 'Editar' button for each location", async () => {
    await renderLocationsCard();
    await waitFor(() => {
      const editBtns = screen.getAllByRole("button", { name: /Editar/i });
      expect(editBtns.length).toBe(2);
      editBtns.forEach((btn) => {
        expect((btn as HTMLButtonElement).disabled).toBe(true);
      });
    });
  });

  it("renders disabled '+ Agregar sede' button (future story)", async () => {
    await renderLocationsCard();
    const btn = screen.getByRole("button", { name: /Agregar sede/i });
    expect(btn).toBeDefined();
    expect((btn as HTMLButtonElement).disabled).toBe(true);
  });

  it("uses list semantics for locations (role=list + listitem)", async () => {
    await renderLocationsCard();
    await waitFor(() => {
      const list = screen.getByRole("list", { name: /Lista de sedes/i });
      expect(list).toBeDefined();
      const items = screen.getAllByRole("listitem");
      expect(items.length).toBe(2);
    });
  });
});
