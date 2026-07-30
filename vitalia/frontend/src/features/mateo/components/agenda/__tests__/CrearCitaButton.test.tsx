/**
 * CrearCitaButton.test.tsx — Vitest unit tests (T-FE-1 reconciled).
 *
 * T-FE-1 vitalia-fase2-mateo-nueva-cita
 * AC-9: Button now pushes to /nueva-cita?origin=... (no modal/dialog).
 *
 * Tests:
 *   - Renders desktop button variant by default
 *   - Button click opens dropdown with 2 options (walk_in, telefono only — existing_patient REMOVED)
 *   - Clicking an option calls router.push with correct URL
 *   - FAB variant renders with fixed bottom-right position classes
 *   - FAB has aria-label="Nueva cita"
 *
 * NOTE: Radix UI DropdownMenu uses Portal — requires userEvent.setup() with
 *       pointer events for trigger interaction in happy-dom. fireEvent.click
 *       does NOT trigger Radix open state.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CrearCitaButton } from "../CrearCitaButton";

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, back: vi.fn() }),
  useParams: () => ({ tenantId: "tenant-123" }),
}));

// Mock Clerk useAuth
vi.mock("@clerk/nextjs", () => ({
  useAuth: vi.fn(() => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    isLoaded: true,
    isSignedIn: true,
  })),
}));

vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

interface RenderProps {
  variant?: "button" | "fab";
}

function renderButton({ variant = "button" }: RenderProps = {}) {
  const qc = makeQueryClient();
  const user = userEvent.setup();
  render(
    <QueryClientProvider client={qc}>
      <CrearCitaButton
        tenantId="tenant-123"
        clinicId="clinic-456"
        variant={variant}
      />
    </QueryClientProvider>,
  );
  return { user };
}

// ── Desktop button tests ──────────────────────────────────────────────────────

describe("CrearCitaButton — desktop variant render", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a button with 'Nueva cita' label", () => {
    renderButton();
    expect(screen.getByText("Nueva cita")).toBeDefined();
  });

  it("button has data-testid=crear-cita-button", () => {
    renderButton();
    expect(screen.getByTestId("crear-cita-button")).toBeDefined();
  });

  it("does NOT render FAB by default", () => {
    renderButton();
    expect(screen.queryByTestId("crear-cita-fab")).toBeNull();
  });
});

// ── Dropdown interaction (AC-9: router.push, no modal) ───────────────────────

describe("CrearCitaButton — dropdown interaction (AC-9)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("opens dropdown showing walk_in option on button click", async () => {
    const { user } = renderButton();
    const button = screen.getByTestId("crear-cita-button");
    await user.click(button);

    await waitFor(() => {
      expect(screen.getByTestId("crear-cita-walk-in")).toBeDefined();
    });
  });

  it("shows 2 dropdown options (walk_in + telefono) after button click", async () => {
    const { user } = renderButton();
    await user.click(screen.getByTestId("crear-cita-button"));

    await waitFor(() => {
      expect(screen.getByTestId("crear-cita-walk-in")).toBeDefined();
      expect(screen.getByTestId("crear-cita-telefono")).toBeDefined();
    });
  });

  it("does NOT show existing_patient option (removed in T-FE-1)", async () => {
    const { user } = renderButton();
    await user.click(screen.getByTestId("crear-cita-button"));

    await waitFor(() => {
      expect(screen.getByTestId("crear-cita-walk-in")).toBeDefined();
    });

    expect(screen.queryByTestId("crear-cita-existing")).toBeNull();
  });

  it("dropdown shows 'Paciente walk-in' label", async () => {
    const { user } = renderButton();
    await user.click(screen.getByTestId("crear-cita-button"));

    await waitFor(() => {
      expect(screen.getByText("Paciente walk-in")).toBeDefined();
    });
  });

  it("dropdown shows 'Reserva telefónica' label", async () => {
    const { user } = renderButton();
    await user.click(screen.getByTestId("crear-cita-button"));

    await waitFor(() => {
      expect(screen.getByText("Reserva telefónica")).toBeDefined();
    });
  });

  it("clicking walk_in calls router.push with origin=walk_in (AC-9: no modal)", async () => {
    const { user } = renderButton();
    await user.click(screen.getByTestId("crear-cita-button"));

    await waitFor(() => {
      expect(screen.getByTestId("crear-cita-walk-in")).toBeDefined();
    });

    await user.click(screen.getByTestId("crear-cita-walk-in"));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(
        "/tenant-123/mateo/agenda/nueva-cita?origin=walk_in",
      );
    });
  });

  it("clicking telefono calls router.push with origin=telefono (AC-9: no modal)", async () => {
    const { user } = renderButton();
    await user.click(screen.getByTestId("crear-cita-button"));

    await waitFor(() => {
      expect(screen.getByTestId("crear-cita-telefono")).toBeDefined();
    });

    await user.click(screen.getByTestId("crear-cita-telefono"));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(
        "/tenant-123/mateo/agenda/nueva-cita?origin=telefono",
      );
    });
  });
});

// ── FAB variant tests ─────────────────────────────────────────────────────────

describe("CrearCitaButton — FAB variant render", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders FAB button instead of text button", () => {
    renderButton({ variant: "fab" });
    expect(screen.getByTestId("crear-cita-fab")).toBeDefined();
    expect(screen.queryByTestId("crear-cita-button")).toBeNull();
  });

  it("FAB has aria-label='Nueva cita'", () => {
    renderButton({ variant: "fab" });
    const fab = screen.getByTestId("crear-cita-fab");
    expect(fab.getAttribute("aria-label")).toBe("Nueva cita");
  });

  it("FAB has 'fixed' class for fixed positioning", () => {
    renderButton({ variant: "fab" });
    const fab = screen.getByTestId("crear-cita-fab");
    expect(fab.className).toContain("fixed");
  });

  it("FAB has 'bottom-4' and 'right-4' positioning classes", () => {
    renderButton({ variant: "fab" });
    const fab = screen.getByTestId("crear-cita-fab");
    expect(fab.className).toContain("bottom-4");
    expect(fab.className).toContain("right-4");
  });

  it("FAB opens dropdown on click showing 2 options", async () => {
    const { user } = renderButton({ variant: "fab" });
    await user.click(screen.getByTestId("crear-cita-fab"));

    await waitFor(() => {
      expect(screen.getByTestId("crear-cita-walk-in")).toBeDefined();
      expect(screen.getByTestId("crear-cita-telefono")).toBeDefined();
    });
  });
});
