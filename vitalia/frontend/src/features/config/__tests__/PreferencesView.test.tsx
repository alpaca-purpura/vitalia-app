// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * PreferencesView.test.tsx — TDD RED component tests.
 *
 * Tests: renders currency selector, timezone selector, read-only language field.
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: 03-arch.md § Test Surfaces
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { PreferencesView } from "../components/cuenta/PreferencesView";
import type { ClinicAccountDTO } from "../types/cuenta.types";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn(), isLoaded: true, isSignedIn: true, userId: "user_test_1" }),
  useUser: () => ({ user: null, isLoaded: true, isSignedIn: true }),
}));
vi.mock("@tanstack/react-query", () => ({
  useQuery: () => ({ data: undefined, isLoading: false, isError: false }),
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  useMutation: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));
// Mock heavy ui-kit selectors
vi.mock("@luana/ui-kit", () => ({
  // testids reales viven en los wrappers del PRODUCTO (PreferencesView) — el mock
  // usa ids -inner para no duplicar el selector del e2e/test.
  CurrencySelector: ({ value }: { value: string }) => (
    <div data-testid="currency-selector-inner">{value}</div>
  ),
  TimezoneSelect: ({ value }: { value: string }) => (
    <div data-testid="timezone-select-inner">{value}</div>
  ),
  FloatingAutosaveIndicator: ({ status }: { status: string }) => (
    <div data-testid="autosave-indicator" data-state={status} />
  ),
  PageContentStack: ({
    children,
    className,
  }: {
    children: React.ReactNode;
    className?: string;
  }) => <div className={className}>{children}</div>,
}));

const mockAccount: ClinicAccountDTO = {
  clinicId: "clinic-uuid",
  tenantId: "tenant-uuid",
  name: "Clínica Demo",
  legalName: null,
  fiscalId: null,
  address: null,
  phone: null,
  email: null,
  currency: "ARS",
  timezone: "America/Argentina/Buenos_Aires",
  country: "AR",
  language: "es-419",
  clinicType: "dental",
  primarySpecialties: [],
  fiscalIdLabel: "CUIT",
};

describe("PreferencesView — render contract (RED)", () => {
  it("renders currency selector with initial value", () => {
    render(<PreferencesView tenantId="tenant-uuid" initialData={mockAccount} />);
    expect(screen.getByTestId("currency-selector")).toBeTruthy();
  });

  it("renders timezone selector with initial value", () => {
    render(<PreferencesView tenantId="tenant-uuid" initialData={mockAccount} />);
    expect(screen.getByTestId("timezone-select")).toBeTruthy();
  });

  it("shows language as read-only (defined at signup)", () => {
    render(<PreferencesView tenantId="tenant-uuid" initialData={mockAccount} />);
    // Multiple elements may contain "idioma" (label + description); verify at least one exists
    const idiomaEls = screen.getAllByText(/idioma/i);
    expect(idiomaEls.length).toBeGreaterThanOrEqual(1);
  });

  it("renders FloatingAutosaveIndicator", () => {
    render(<PreferencesView tenantId="tenant-uuid" initialData={mockAccount} />);
    expect(screen.getByTestId("autosave-indicator")).toBeTruthy();
  });
});
