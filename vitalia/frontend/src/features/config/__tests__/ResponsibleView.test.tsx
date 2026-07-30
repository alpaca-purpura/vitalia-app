// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * ResponsibleView.test.tsx — TDD RED component tests.
 *
 * Tests: renders DPO name/email if available, shows link to seguridad, empty state.
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: 03-arch.md § Test Surfaces
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ResponsibleView } from "../components/cuenta/ResponsibleView";
import type { DpoReferenceDTO } from "../types/cuenta.types";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn(), isLoaded: true, isSignedIn: true }),
}));
vi.mock("@tanstack/react-query", () => ({
  useQuery: () => ({ data: undefined, isLoading: false, isError: false }),
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
}));

const mockDpo: DpoReferenceDTO = {
  name: "Dr. Juan García",
  email: "dpo@clinicademo.com",
  roleLabel: "Responsable de tratamiento de datos",
  manageUrlSubpath: "config/seguridad",
};

describe("ResponsibleView — render contract (RED)", () => {
  it("shows DPO name when available", () => {
    render(
      <ResponsibleView
        tenantId="tenant-uuid"
        dpoData={mockDpo}
      />,
    );
    expect(screen.getByText("Dr. Juan García")).toBeTruthy();
  });

  it("shows link to seguridad section", () => {
    render(
      <ResponsibleView
        tenantId="tenant-uuid"
        dpoData={mockDpo}
      />,
    );
    const link = screen.getByRole("link");
    expect(link).toBeTruthy();
    expect(link.getAttribute("href")).toContain("seguridad");
  });

  it("shows empty state when no DPO configured", () => {
    render(
      <ResponsibleView
        tenantId="tenant-uuid"
        dpoData={{ name: null, email: null, roleLabel: "Responsable", manageUrlSubpath: "config/seguridad" }}
      />,
    );
    expect(screen.getByText(/sin configurar|no configurado|aún no/i)).toBeTruthy();
  });

  it("has accessible container", () => {
    const { container } = render(
      <ResponsibleView tenantId="tenant-uuid" dpoData={mockDpo} />,
    );
    expect(container.querySelector("[data-testid='responsible-view']")).toBeTruthy();
  });
});
