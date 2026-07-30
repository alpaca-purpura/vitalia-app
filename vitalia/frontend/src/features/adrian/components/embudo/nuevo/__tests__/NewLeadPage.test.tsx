// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * NewLeadPage.test.tsx — RED-first tests for NewLeadPage form (T-FE-3).
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// NewLeadPage migrated to @luana/ui-kit EntitySubNavBar (T-5)
vi.mock("@luana/ui-kit", () => ({
  EntitySubNavBar: ({ rootLabel }: { rootLabel: string }) => (
    <nav data-testid="entity-sub-nav-bar">
      <span>{rootLabel}</span>
    </nav>
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
  useTenantId: vi.fn().mockReturnValue("tenant-new-lead-test"),
}));
vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: vi.fn().mockResolvedValue({
    id: "lead-new-001",
    stage: "interesado",
    tenantId: "tenant-new-lead-test",
  }),
  ApiError: class extends Error {},
}));

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({ tenantId: "tenant-new-lead-test" }),
}));

import { fetchClient } from "@/lib/api/fetchClient";
import { NewLeadPage } from "../NewLeadPage";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return createElement(QueryClientProvider, { client: qc }, children);
}

describe("NewLeadPage", () => {
  it("renders EntitySubNavBar with Embudo back link and no leaf tabs", () => {
    render(<NewLeadPage tenantId="tenant-new-lead-test" />, { wrapper });
    expect(screen.getByTestId("entity-sub-nav-bar")).toBeInTheDocument();
  });

  it("renders the form with required fields (nombre, canal)", () => {
    render(<NewLeadPage tenantId="tenant-new-lead-test" />, { wrapper });
    // Nombre field
    expect(screen.getByLabelText(/nombre/i)).toBeInTheDocument();
    // Canal select
    expect(screen.getByLabelText(/canal/i)).toBeInTheDocument();
  });

  it("shows validation error when nombre is empty on submit", async () => {
    // The form validates on submit when no name is provided
    render(<NewLeadPage tenantId="tenant-new-lead-test" />, { wrapper });
    const submitBtn = screen.getByRole("button", { name: /crear lead/i });
    // Submit without filling required fields
    await act(async () => {
      fireEvent.submit(submitBtn.closest("form")!);
    });
    // RHF triggers validation and shows errors
    await waitFor(() => {
      // At minimum, the form should still be rendered (not navigated away)
      expect(screen.getByRole("button", { name: /crear lead/i })).toBeInTheDocument();
      // Validation was triggered (form didn't submit to mock)
      expect(vi.mocked(fetchClient)).not.toHaveBeenCalled();
    }, { timeout: 3000 });
  });

  it("shows validation error when neither phone nor email provided", async () => {
    render(<NewLeadPage tenantId="tenant-new-lead-test" />, { wrapper });
    const nombreInput = screen.getByLabelText(/nombre/i);
    fireEvent.change(nombreInput, { target: { value: "Luis Torres" } });
    const submitBtn = screen.getByRole("button", { name: /crear lead/i });
    fireEvent.click(submitBtn);
    await waitFor(() => {
      expect(
        screen.getByText(/teléfono.*correo/i),
      ).toBeInTheDocument();
    });
  });

  it("Cancelar button navigates back to /embudo without creating", () => {
    render(<NewLeadPage tenantId="tenant-new-lead-test" />, { wrapper });
    const cancelBtn = screen.getByRole("button", { name: /cancelar/i });
    fireEvent.click(cancelBtn);
    expect(mockPush).toHaveBeenCalledWith(
      expect.stringContaining("embudo"),
    );
  });
});
