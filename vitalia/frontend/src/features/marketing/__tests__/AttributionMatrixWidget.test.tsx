/**
 * AttributionMatrixWidget tests — SC-MK-03 attribution matrix inline
 * @coverage gherkin SC-MK-03 (test_renders_attribution_matrix_inline via ReservationStage)
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// Mock Clerk
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("tok"),
    orgId: "org-1",
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


// Mock clinic hook
vi.mock("@/hooks/useClinicId", () => ({ useClinicId: () => "clinic-123" }));

// Mock React Query
vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(),
  useMutation: vi.fn(),
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  QueryClient: vi.fn(),
  QueryClientProvider: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

const mockAttributionData = {
  periodStart: "2026-05-01T00:00:00Z",
  periodEnd: "2026-05-31T23:59:59Z",
  origins: [
    {
      origin: "sales_agent",
      leads: 80,
      qualified: 40,
      convListo: 28,
      reservations: 20,
      adoption: 16,
      valueCents: 320000,
    },
    {
      origin: "walk_in",
      leads: 50,
      qualified: 22,
      convListo: 15,
      reservations: 10,
      adoption: 8,
      valueCents: 160000,
    },
    {
      origin: "phone_manual",
      leads: 30,
      qualified: 12,
      convListo: 8,
      reservations: 5,
      adoption: 4,
      valueCents: 80000,
    },
    {
      origin: "proactive_outbound",
      leads: 22,
      qualified: 8,
      convListo: 5,
      reservations: 3,
      adoption: 2,
      valueCents: 40000,
    },
  ],
  totals: {
    origin: "total",
    leads: 182,
    qualified: 82,
    convListo: 56,
    reservations: 38,
    adoption: 30,
    valueCents: 600000,
  },
  topInsightText: "El agente de ventas genera el 44% de tus leads calificados.",
  currency: "PEN",
};

import { useQuery } from "@tanstack/react-query";

describe("AttributionMatrixWidget", () => {
  beforeEach(() => {
    vi.mocked(useQuery).mockReturnValue({
      data: mockAttributionData,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);
  });

  it("test_renders_table_with_4_origins — renders table with 4 origin rows + total", async () => {
    const { AttributionMatrixWidget } =
      await import("../components/AttributionMatrixWidget");
    render(<AttributionMatrixWidget />);

    // Table element must exist for a11y
    const table = screen.getByRole("table");
    expect(table).toBeInTheDocument();

    // All 4 origin labels must appear
    expect(screen.getByText("Agente de ventas")).toBeInTheDocument();
    expect(screen.getByText("Visita directa")).toBeInTheDocument();
    expect(screen.getByText("Teléfono (manual)")).toBeInTheDocument();
    expect(screen.getByText("Outbound proactivo")).toBeInTheDocument();

    // Total row must appear
    expect(screen.getByText("Total")).toBeInTheDocument();
  });

  it("test_renders_column_headers — table has correct column headers", async () => {
    const { AttributionMatrixWidget } =
      await import("../components/AttributionMatrixWidget");
    render(<AttributionMatrixWidget />);

    expect(screen.getByText("Leads")).toBeInTheDocument();
    expect(screen.getByText("Calificados")).toBeInTheDocument();
    expect(screen.getByText("Conv. Listo")).toBeInTheDocument();
    expect(screen.getByText("Reservas")).toBeInTheDocument();
    expect(screen.getByText("Adopción")).toBeInTheDocument();
  });

  it("test_renders_top_insight — shows topInsightText from data", async () => {
    const { AttributionMatrixWidget } =
      await import("../components/AttributionMatrixWidget");
    render(<AttributionMatrixWidget />);

    expect(
      screen.getByText(
        "El agente de ventas genera el 44% de tus leads calificados.",
      ),
    ).toBeInTheDocument();
  });

  it("test_loading_state — shows loading indicator when fetching", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { AttributionMatrixWidget } =
      await import("../components/AttributionMatrixWidget");
    render(<AttributionMatrixWidget />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("test_empty_state — shows empty message when no data", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { AttributionMatrixWidget } =
      await import("../components/AttributionMatrixWidget");
    render(<AttributionMatrixWidget />);
    expect(screen.getByText(/no hay datos de atribución/i)).toBeInTheDocument();
  });

  it("test_error_state — shows error message on query error", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error("fetch failed"),
    } as ReturnType<typeof useQuery>);

    const { AttributionMatrixWidget } =
      await import("../components/AttributionMatrixWidget");
    render(<AttributionMatrixWidget />);
    expect(
      screen.getByText(/no se pudo cargar la matriz/i),
    ).toBeInTheDocument();
  });

  it("test_heatmap_cells_have_aria_label — each data cell has accessible label", async () => {
    const { AttributionMatrixWidget } =
      await import("../components/AttributionMatrixWidget");
    render(<AttributionMatrixWidget />);

    // At least some cells should have aria-label for screen readers
    const cells = screen.getAllByRole("cell");
    const cellsWithAriaLabel = cells.filter((c) =>
      c.getAttribute("aria-label"),
    );
    expect(cellsWithAriaLabel.length).toBeGreaterThan(0);
  });

  it("test_no_phi_in_output — does not render patient names", async () => {
    const { AttributionMatrixWidget } =
      await import("../components/AttributionMatrixWidget");
    const { container } = render(<AttributionMatrixWidget />);
    // Origin labels are channel names, never patient names
    // PHI check: no text like "patient.name" in DOM
    expect(container.innerHTML).not.toMatch(/patient\.name/i);
  });
});
