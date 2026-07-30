/**
 * TenantSwitcher.test.tsx — Vitest unit tests (TDD RED→GREEN).
 *
 * Bug #2 (vitalia-bugfix-shell-nav-scroll-errors T-4):
 *   El selector de tenant debe verse SIEMPRE que haya ≥1 tenant disponible,
 *   aunque el activeTenant aún no esté resuelto (ventana pre-rehydration /
 *   pre-auto-pick). Antes `if (!activeTenant && !isLoading) return null;`
 *   ocultaba el trigger en esa ventana → selector invisible con 1 tenant.
 *
 * RN-2: selector visible con ≥1 tenant · oculto con 0 tenants (graceful degrade).
 *
 * downstream-regression-na: brand-local shell-organism test; no cross-brand consumers
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import type { Tenant } from "./types";

// ── Mocks ────────────────────────────────────────────────────────────────────
vi.mock("next/navigation", () => ({
  usePathname: vi.fn(() => "/test-tenant/lisa/marca"),
}));

const mockUseTenants = vi.fn();
vi.mock("@/hooks/useTenants", () => ({
  useTenants: () => mockUseTenants(),
}));

// useTenantStore is a selector-based zustand hook: useTenantStore((s) => s.x)
// We drive it with a controllable state object.
let storeState: {
  activeTenant: Tenant | null;
  availableTenants: ReadonlyArray<Tenant>;
  switchTenant: (id: string) => Tenant | null;
};
vi.mock("@/stores/tenant-store", () => ({
  useTenantStore: (selector: (s: typeof storeState) => unknown) =>
    selector(storeState),
}));

import { TenantSwitcher } from "./TenantSwitcher";

const TENANT_A: Tenant = { id: "clinic-a", name: "Clínica Sanaré", city: "CDMX" };

beforeEach(() => {
  vi.clearAllMocks();
  mockUseTenants.mockReturnValue({
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  });
  storeState = {
    activeTenant: null,
    availableTenants: [],
    switchTenant: vi.fn(() => null),
  };
});

describe("TenantSwitcher — Bug #2 single-tenant visibility (RN-2)", () => {
  it("RED→GREEN: con 1 tenant disponible + activeTenant ya resuelto → trigger visible", () => {
    storeState.activeTenant = TENANT_A;
    storeState.availableTenants = [TENANT_A];
    render(<TenantSwitcher />);
    expect(screen.getByTestId("tenant-switcher-trigger")).toBeInTheDocument();
  });

  it("RED→GREEN: con 1 tenant disponible PERO activeTenant aún null (ventana pre-pick) → trigger visible (no null)", () => {
    // Esta es la ventana del Bug #2: availableTenants tiene 1 item pero activeTenant
    // todavía no se resolvió (rehydration/auto-pick pendiente). Antes retornaba null.
    storeState.activeTenant = null;
    storeState.availableTenants = [TENANT_A];
    render(<TenantSwitcher />);
    expect(screen.getByTestId("tenant-switcher-trigger")).toBeInTheDocument();
  });

  it("loading state → trigger visible (skeleton dentro del trigger)", () => {
    mockUseTenants.mockReturnValue({
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    });
    storeState.activeTenant = null;
    storeState.availableTenants = [];
    render(<TenantSwitcher />);
    expect(screen.getByTestId("tenant-switcher-trigger")).toBeInTheDocument();
  });

  it("0 tenants (graceful degrade) → no trigger (comportamiento preservado)", () => {
    storeState.activeTenant = null;
    storeState.availableTenants = [];
    const { container } = render(<TenantSwitcher />);
    expect(screen.queryByTestId("tenant-switcher-trigger")).toBeNull();
    expect(container.firstChild).toBeNull();
  });
});
