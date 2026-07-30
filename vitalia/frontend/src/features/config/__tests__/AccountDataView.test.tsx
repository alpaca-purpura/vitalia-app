// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * AccountDataView.test.tsx — TDD RED component tests.
 *
 * Tests: renders editable fields, shows read-only badges for country/language/clinicType,
 * renders SpecialtiesField, shows autosave indicator, accessible markup.
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: 03-arch.md § Test Surfaces
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AccountDataView } from "../components/cuenta/AccountDataView";
import type { ClinicAccountDTO } from "../types/cuenta.types";

// Minimal mocks for external deps
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn(), isLoaded: true, isSignedIn: true, userId: "user_test_1" }),
  useUser: () => ({ user: null, isLoaded: true, isSignedIn: true }),
}));
vi.mock("@tanstack/react-query", () => ({
  useQuery: () => ({ data: undefined, isLoading: false, isError: false }),
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  useMutation: () => ({ mutateAsync: vi.fn(), isPending: false }),
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
  primarySpecialties: ["Odontología cosmética"],
  fiscalIdLabel: "CUIT",
};

describe("AccountDataView — render contract (RED)", () => {
  it("renders editable name field", () => {
    render(
      <AccountDataView
        tenantId="tenant-uuid"
        initialData={mockAccount}
      />,
    );
    expect(screen.getByLabelText(/Nombre comercial/i)).toBeTruthy();
  });

  it("shows read-only badge for country (defined at signup)", () => {
    render(
      <AccountDataView
        tenantId="tenant-uuid"
        initialData={mockAccount}
      />,
    );
    // Should show at least one read-only indicator (country/language/clinicType all show it)
    const badges = screen.getAllByText(/definido en el alta/i);
    expect(badges.length).toBeGreaterThanOrEqual(1);
  });

  it("renders specialties multi-select field", () => {
    render(
      <AccountDataView
        tenantId="tenant-uuid"
        initialData={mockAccount}
      />,
    );
    expect(screen.getByTestId("specialties-field")).toBeTruthy();
  });

  it("renders FloatingAutosaveIndicator", () => {
    render(
      <AccountDataView
        tenantId="tenant-uuid"
        initialData={mockAccount}
      />,
    );
    expect(screen.getByTestId("autosave-indicator")).toBeTruthy();
  });

  it("container has data-testid", () => {
    const { container } = render(
      <AccountDataView
        tenantId="tenant-uuid"
        initialData={mockAccount}
      />,
    );
    expect(container.querySelector("[data-testid='account-data-view']")).toBeTruthy();
  });
});
