// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * PublicLinkBar.test.tsx — Vitest + RTL tests.
 *
 * Covers:
 *   SC-D3D-9:  Borrador pill when visibleEnLanding=false
 *   SC-D3D-10: Publicada pill when visibleEnLanding=true
 *   SC-D3D-11: Publicar button enabled when slug exists
 *   SC-D3D-12: Ocultar button shown when already public
 *   SC-D3D-13: Copy button disabled when no public URL
 *   SC-D3D-14: toggle mutation called on button click
 *
 * T-FE-pagina-publica vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-D.4
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PublicLinkBar } from "./PublicLinkBar";
import type { DoctorDetail } from "../../../../types/staff.types";

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockToggle = vi.fn();

vi.mock("../../../../api/staff", () => ({
  useTogglePublicVisible: vi.fn(() => ({
    mutate: mockToggle,
    isPending: false,
    isError: false,
  })),
}));

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({ push: vi.fn() })),
  usePathname: vi.fn(() => "/tenant-1/lisa/staff/doc-1/pagina"),
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={makeQC()}>
      {children}
    </QueryClientProvider>
  );
}

const draftDoctor: DoctorDetail = {
  id: "doc-1",
  firstName: "Ana",
  lastName: "García",
  dni: "12345678",
  email: "ana@example.com",
  credential: "12345",
  credentialCountry: "PE",
  languages: [],
  bioLinks: [],
    active: true,
  createdAt: "2026-01-01T00:00:00Z",
  updatedAt: "2026-01-01T00:00:00Z",
  publicSlug: "ana-garcia", clinicSlug: "sonrisas-lima",
  visibleEnLanding: false,
};

const publicDoctor: DoctorDetail = {
  ...draftDoctor,
  visibleEnLanding: true,
};

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("PublicLinkBar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("SC-D3D-9: Borrador pill when visibleEnLanding=false", () => {
    render(<PublicLinkBar doctorId="doc-1" doctor={draftDoctor} />, { wrapper: Wrapper });

    expect(screen.getByText("Borrador")).toBeTruthy();
  });

  it("SC-D3D-10: Publicada pill when visibleEnLanding=true", () => {
    render(<PublicLinkBar doctorId="doc-1" doctor={publicDoctor} />, { wrapper: Wrapper });

    expect(screen.getByText("Publicada")).toBeTruthy();
  });

  it("SC-D3D-11: Publicar button shown when draft + slug exists", () => {
    render(<PublicLinkBar doctorId="doc-1" doctor={draftDoctor} />, { wrapper: Wrapper });

    expect(screen.getByRole("button", { name: /publicar perfil/i })).toBeTruthy();
  });

  it("SC-D3D-12: Ocultar button shown when already public", () => {
    render(<PublicLinkBar doctorId="doc-1" doctor={publicDoctor} />, { wrapper: Wrapper });

    expect(screen.getByRole("button", { name: /ocultar perfil/i })).toBeTruthy();
  });

  it("SC-D3D-13: Copy button disabled when no public URL (no slug)", () => {
    const noSlugDoctor: DoctorDetail = { ...draftDoctor, publicSlug: null };
    render(<PublicLinkBar doctorId="doc-1" doctor={noSlugDoctor} />, { wrapper: Wrapper });

    const copyBtn = screen.getByRole("button", { name: /copiar enlace/i });
    expect((copyBtn as HTMLButtonElement).disabled).toBe(true);
  });

  it("SC-D3D-14: toggle mutation called when Publicar clicked", () => {
    render(<PublicLinkBar doctorId="doc-1" doctor={draftDoctor} />, { wrapper: Wrapper });

    fireEvent.click(screen.getByRole("button", { name: /publicar perfil/i }));
    expect(mockToggle).toHaveBeenCalledWith(true);
  });

  it("SC-D3D-15: toggle mutation called with false when Ocultar clicked", () => {
    render(<PublicLinkBar doctorId="doc-1" doctor={publicDoctor} />, { wrapper: Wrapper });

    fireEvent.click(screen.getByRole("button", { name: /ocultar perfil/i }));
    expect(mockToggle).toHaveBeenCalledWith(false);
  });
});
