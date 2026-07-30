/**
 * LucasStageRecommendationsCard tests — SC-MK-01 top 3 cards, expand, click → DetailModal
 * @coverage gherkin SC-MK-01 (test_renders_top_3_cards)
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

// Mock nuqs
vi.mock("nuqs", () => {
  const makeParser = () => ({
    withDefault: (_d: unknown) => ({
      withOptions: (_opts: unknown) => ({
        defaultValue: _d,
        parseServerSide: (v: unknown) => v,
      }),
      defaultValue: _d,
      parseServerSide: (v: unknown) => v,
    }),
    withOptions: (_opts: unknown) => ({
      withDefault: (_d: unknown) => ({
        defaultValue: _d,
        parseServerSide: (v: unknown) => v,
      }),
      defaultValue: undefined,
      parseServerSide: (v: unknown) => v,
    }),
    defaultValue: undefined,
    parseServerSide: (v: unknown) => v,
  });
  return {
    useQueryState: (_key: string, _parser: unknown) => [null, vi.fn()],
    parseAsStringEnum: (_values: string[]) => makeParser(),
    parseAsString: makeParser(),
    parseAsBoolean: makeParser(),
  };
});

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

const mockRecs = [
  {
    id: "rec-1",
    tenantId: "org-1",
    clinicId: "clinic-123",
    stage: "attraction",
    recommendationKind: "scale_meta",
    title: "Aumentar presupuesto Meta Ads",
    body: "Tu CPL está 20% por debajo del benchmark sectorial.",
    rationaleJson: { metric: "cpl", value: 24, benchmark: 30 },
    actionPayloadJson: { budget_delta_pct: 20 },
    priority: 1,
    confidencePct: 87,
    projectedImpactText: "+15 pacientes/mes estimados",
    status: "open",
    approvedByUserId: null,
    approvedAt: null,
    undoUntil: null,
    expiresAt: "2026-06-01T00:00:00Z",
    createdAt: "2026-05-20T00:00:00Z",
  },
  {
    id: "rec-2",
    tenantId: "org-1",
    clinicId: "clinic-123",
    stage: "attraction",
    recommendationKind: "enable_retargeting",
    title: "Activar retargeting",
    body: "El 60% de tus leads no retornan sin retargeting.",
    rationaleJson: {},
    actionPayloadJson: null,
    priority: 2,
    confidencePct: 72,
    projectedImpactText: "+8 pacientes/mes estimados",
    status: "open",
    approvedByUserId: null,
    approvedAt: null,
    undoUntil: null,
    expiresAt: "2026-06-01T00:00:00Z",
    createdAt: "2026-05-20T00:00:00Z",
  },
  {
    id: "rec-3",
    tenantId: "org-1",
    clinicId: "clinic-123",
    stage: "qualification",
    recommendationKind: "speed_lead_response",
    title: "Respuesta rápida a leads",
    body: "Reduce el tiempo de respuesta a menos de 5 minutos.",
    rationaleJson: {},
    actionPayloadJson: null,
    priority: 3,
    confidencePct: 65,
    projectedImpactText: "+5 citas/mes estimadas",
    status: "open",
    approvedByUserId: null,
    approvedAt: null,
    undoUntil: null,
    expiresAt: "2026-06-01T00:00:00Z",
    createdAt: "2026-05-20T00:00:00Z",
  },
  {
    id: "rec-4",
    tenantId: "org-1",
    clinicId: "clinic-123",
    stage: "reservation",
    recommendationKind: "reduce_no_shows",
    title: "Reducir ausencias con recordatorios",
    body: "Enviar SMS 24h antes reduce ausencias un 30%.",
    rationaleJson: {},
    actionPayloadJson: null,
    priority: 4,
    confidencePct: 80,
    projectedImpactText: "+3 citas/mes estimadas",
    status: "open",
    approvedByUserId: null,
    approvedAt: null,
    undoUntil: null,
    expiresAt: "2026-06-01T00:00:00Z",
    createdAt: "2026-05-20T00:00:00Z",
  },
];

import { useQuery } from "@tanstack/react-query";

describe("LucasStageRecommendationsCard", () => {
  beforeEach(() => {
    vi.mocked(useQuery).mockReturnValue({
      data: { items: mockRecs },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);
  });

  it("test_renders_top_3_cards — shows top 3 priority recommendations by default (SC-MK-01)", async () => {
    const { LucasStageRecommendationsCard } =
      await import("../components/LucasStageRecommendationsCard");
    // No stage filter — shows all 4 recs cross-stage, top 3 visible
    render(<LucasStageRecommendationsCard />);

    // Top 3 cards should be visible (priority 1, 2, 3)
    expect(
      screen.getByText("Aumentar presupuesto Meta Ads"),
    ).toBeInTheDocument();
    expect(screen.getByText("Activar retargeting")).toBeInTheDocument();
    expect(screen.getByText("Respuesta rápida a leads")).toBeInTheDocument();

    // 4th card should NOT be visible (collapsed)
    expect(
      screen.queryByText("Reducir ausencias con recordatorios"),
    ).not.toBeInTheDocument();
  });

  it("test_expand_shows_all — clicking 'Ver todas' shows all recommendations", async () => {
    const { LucasStageRecommendationsCard } =
      await import("../components/LucasStageRecommendationsCard");
    // No stage filter — shows all 4 recs cross-stage
    render(<LucasStageRecommendationsCard />);

    // Initially 4th card hidden
    expect(
      screen.queryByText("Reducir ausencias con recordatorios"),
    ).not.toBeInTheDocument();

    // Click expand button (text includes count: "Ver todas (4)")
    const expandBtn = screen.getByRole("button", { name: /ver todas/i });
    fireEvent.click(expandBtn);

    // Now 4th card should be visible
    expect(
      screen.getByText("Reducir ausencias con recordatorios"),
    ).toBeInTheDocument();
  });

  it("test_loading_state — shows loading indicator when fetching", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { LucasStageRecommendationsCard } =
      await import("../components/LucasStageRecommendationsCard");
    render(<LucasStageRecommendationsCard stage="attraction" />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("test_empty_state — shows empty message when no recommendations", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: { items: [] },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { LucasStageRecommendationsCard } =
      await import("../components/LucasStageRecommendationsCard");
    render(<LucasStageRecommendationsCard stage="attraction" />);
    expect(
      screen.getByText(/no hay recomendaciones activas/i),
    ).toBeInTheDocument();
  });

  it("test_card_click_opens_detail_modal — clicking card opens LucasRecommendationDetailModal", async () => {
    const { LucasStageRecommendationsCard } =
      await import("../components/LucasStageRecommendationsCard");
    render(<LucasStageRecommendationsCard stage="attraction" />);

    const firstCard = screen.getByText("Aumentar presupuesto Meta Ads");
    fireEvent.click(firstCard);

    // DetailModal should appear with the recommendation data
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });
});
