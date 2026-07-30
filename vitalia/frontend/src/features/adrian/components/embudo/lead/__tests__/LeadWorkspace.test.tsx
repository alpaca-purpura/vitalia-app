// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * LeadWorkspace.test.tsx — RED-first tests for LeadWorkspace component (T-FE-3).
 * TDD: RED before implementation per tdd-mandatory.md.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

// Mock @luana/ui-kit EntityWorkspaceLayout — LeadWorkspace migrated to kit (T-5)
vi.mock("@luana/ui-kit", () => ({
  EntityWorkspaceLayout: ({
    rootLabel,
    entity,
    activeLeaf,
    children,
  }: {
    rootLabel: string;
    entity: { name: string } | null;
    activeLeaf: string | null;
    children: React.ReactNode;
  }) => (
    <div data-testid="entity-workspace-layout">
      <nav data-testid="entity-sub-nav-bar">
        <span data-testid="root-label">{rootLabel}</span>
        {entity && <span data-testid="entity-name">{entity.name}</span>}
        {activeLeaf && <span data-testid="active-leaf">{activeLeaf}</span>}
      </nav>
      <div data-testid="entity-workspace-content">{children}</div>
    </div>
  ),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: vi.fn().mockReturnValue("tenant-workspace-test"),
}));
vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: vi.fn().mockResolvedValue({}),
  ApiError: class extends Error {},
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({ leadId: "lead-001", tenantId: "tenant-workspace-test" }),
}));

import { LeadWorkspace } from "../LeadWorkspace";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return createElement(QueryClientProvider, { client: qc }, children);
}

describe("LeadWorkspace", () => {
  it("renders EntitySubNavBar with back link (rootLabel = Embudo)", async () => {
    render(
      <LeadWorkspace
        tenantId="tenant-workspace-test"
        leadId="lead-001"
        activeLeaf="resumen"
      >
        <div data-testid="content">Resumen content</div>
      </LeadWorkspace>,
      { wrapper },
    );
    const { waitFor } = await import("@testing-library/react");
    // EntitySubNavBar always renders (even before data loads)
    expect(screen.getByTestId("entity-sub-nav-bar")).toBeInTheDocument();
    expect(screen.getByTestId("root-label")).toHaveTextContent("Embudo");
    // Active leaf appears once entity data is loaded
    await waitFor(() => {
      expect(screen.getByTestId("active-leaf")).toHaveTextContent("resumen");
    });
  });

  it("renders children inside the workspace", async () => {
    render(
      <LeadWorkspace
        tenantId="tenant-workspace-test"
        leadId="lead-001"
        activeLeaf="historial"
      >
        <div data-testid="historial-content">Historial</div>
      </LeadWorkspace>,
      { wrapper },
    );
    // Children render once loading completes
    const { waitFor } = await import("@testing-library/react");
    await waitFor(() => {
      expect(screen.getByTestId("historial-content")).toBeInTheDocument();
    });
  });

  it("shows loading skeleton when data is not yet available", () => {
    render(
      <LeadWorkspace
        tenantId="tenant-workspace-test"
        leadId="lead-001"
        activeLeaf="resumen"
      >
        <div>Content</div>
      </LeadWorkspace>,
      { wrapper },
    );
    // EntitySubNavBar renders even in loading state
    expect(screen.getByTestId("entity-sub-nav-bar")).toBeInTheDocument();
  });
});
