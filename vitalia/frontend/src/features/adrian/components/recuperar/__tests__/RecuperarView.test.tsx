// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * RecuperarView.test.tsx — RED-first tests for RecuperarView (T-FE-3).
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: vi.fn().mockReturnValue("tenant-recuperar-test"),
}));
vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: vi.fn(),
  ApiError: class extends Error {},
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({ tenantId: "tenant-recuperar-test" }),
}));

import { fetchClient } from "@/lib/api/fetchClient";
import { RecuperarView } from "../RecuperarView";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";

const MOCK_FROZEN = {
  recienCongelados: [
    {
      id: "lead-010",
      tenantId: "tenant-recuperar-test",
      name: "Lucía R███",
      lastStage: "calificando",
      frozenReason: "inactividad_lead",
      frozenAt: "2026-05-28T10:00:00Z",
      channel: "whatsapp",
      score: 32,
      closureReason: null,
      reactivationCohortAt: null,
    },
  ],
  decidioNo: [
    {
      id: "lead-012",
      tenantId: "tenant-recuperar-test",
      name: "Iván S███",
      lastStage: "plan_presentado",
      frozenReason: null,
      frozenAt: null,
      channel: null,
      score: null,
      closureReason: "precio",
      reactivationCohortAt: "2026-08-28T10:00:00Z",
    },
  ],
};

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false, retryDelay: 0, gcTime: 0 },
    },
  });
  return createElement(QueryClientProvider, { client: qc }, children);
}

describe("RecuperarView", () => {
  beforeEach(() => {
    vi.mocked(fetchClient).mockReset();
  });

  it("shows loading state initially", () => {
    vi.mocked(fetchClient).mockImplementation(() => new Promise(() => {})); // never resolves
    render(<RecuperarView tenantId="tenant-recuperar-test" />, { wrapper });
    // aria-busy or skeleton present
    const busyEl = document.querySelector('[aria-busy="true"]');
    expect(busyEl).not.toBeNull();
  });

  it("shows empty state when no frozen leads", async () => {
    vi.mocked(fetchClient).mockResolvedValueOnce({
      recienCongelados: [],
      decidioNo: [],
    });
    render(<RecuperarView tenantId="tenant-recuperar-test" />, { wrapper });
    const { waitFor } = await import("@testing-library/react");
    await waitFor(() => {
      expect(screen.getByText(/sin leads para recuperar/i)).toBeInTheDocument();
    });
  });

  it("renders frozen lead rows when data is available", async () => {
    vi.mocked(fetchClient).mockResolvedValueOnce(MOCK_FROZEN);
    render(<RecuperarView tenantId="tenant-recuperar-test" />, { wrapper });
    const { waitFor } = await import("@testing-library/react");
    await waitFor(() => {
      // Should show section headings
      const congeladosEl = screen.queryByText(/congelados/i);
      expect(congeladosEl).not.toBeNull();
    });
  });
});
