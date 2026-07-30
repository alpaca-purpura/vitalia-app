// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * DoctorPaginaView.test.tsx — Vitest + RTL tests for Página workspace leaf.
 *
 * Covers:
 *   SC-D3D-1: loading skeleton renders when data loading
 *   SC-D3D-2: "never" state shows ✨ Generar perfil CTA
 *   SC-D3D-3: "quiet" state shows last generation date + Regenerar
 *   SC-D3D-4: "material_new" state shows ⚡ banner + Actualizar
 *   SC-D3D-5: generate mutation called on CTA click
 *   SC-D3D-6: confirm modal appears when profile exists + user clicks Generar
 *   SC-D3D-7: error state shows error message
 *   SC-D3D-8: PublicLinkBar rendered
 *   SC-D3B-pagina-1: BioRepoInputs mounts on Página tab (material del doctor section)
 *
 * T-FE-pagina-publica vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-D
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { DoctorDetail } from "../../../../types/staff.types";

// ── Module mocks ──────────────────────────────────────────────────────────────

const mockMutate = vi.fn();
const mockMutateAsync = vi.fn().mockResolvedValue(undefined);

vi.mock("../../../../api/staff", () => ({
  useDoctor: vi.fn(),
  useGenerateProfile: vi.fn(() => ({
    mutate: mockMutate,
    mutateAsync: mockMutateAsync,
    isPending: false,
    isError: false,
  })),
  useTogglePublicVisible: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
  })),
  useSavePublicProfile: vi.fn(() => ({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    isPending: false,
  })),
  // BioRepoInputs hooks (needed since BioRepoInputs mounts on Página)
  usePatchDoctor: vi.fn(() => ({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
  })),
  useBioFiles: vi.fn(() => ({
    data: [],
    isLoading: false,
    isError: false,
  })),
  useBioFileUpload: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
  useDeleteBioFile: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
  })),
  useBioFileDownload: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
  })),
  staffKeys: {
    detail: vi.fn(() => ["lisa", "staff", "detail", "test-id"]),
    all: ["lisa", "staff"],
    lists: vi.fn(() => ["lisa", "staff", "list"]),
    list: vi.fn(() => ["lisa", "staff", "list", {}]),
    details: vi.fn(() => ["lisa", "staff", "detail"]),
    blocks: vi.fn(() => ["lisa", "staff", "detail", "test-id", "blocks"]),
    bioFiles: vi.fn(() => ["lisa", "staff", "detail", "test-id", "bio-files"]),
    occurrences: vi.fn(() => ["lisa", "staff", "detail", "test-id", "occurrences"]),
  },
}));

// BioRepoInputs also needs Clerk + useTenantId + useClinicId
vi.mock("@clerk/nextjs", () => ({
  useAuth: vi.fn(() => ({
    getToken: vi.fn().mockResolvedValue("test-token"),
    isLoaded: true,
    isSignedIn: true,
  })),
}));

vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: vi.fn(() => "tenant-123"),
}));

vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: vi.fn(() => "clinic-456"),
}));

vi.mock("@/hooks/use-autosave", () => ({
  useAutosave: vi.fn(() => ({
    schedule: vi.fn(),
    status: "idle" as const,
  })),
}));

vi.mock("@/components/shared/FloatingAutosaveIndicator", () => ({
  FloatingAutosaveIndicator: () => null,
}));

// ── Test helpers ──────────────────────────────────────────────────────────────

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={makeQC()}>
      {children}
    </QueryClientProvider>
  );
}

const baseDoctorNeverGenerated: DoctorDetail = {
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
  profileState: { generatedAt: null, materialNew: false, materialNewCount: 0 },
  publicProfile: null,
  publicSlug: null,
  visibleEnLanding: false,
};

const doctorQuietState: DoctorDetail = {
  ...baseDoctorNeverGenerated,
  profileState: { generatedAt: "2026-05-01T10:00:00Z", materialNew: false, materialNewCount: 0 },
  publicProfile: {
    sobreMi: "Médico especializado en...",
    formacion: [],
    experiencia: [],
    tratamientos: [],
    certificaciones: [],
    idiomas: [],
  },
};

const doctorMaterialNew: DoctorDetail = {
  ...doctorQuietState,
  profileState: { generatedAt: "2026-05-01T10:00:00Z", materialNew: true, materialNewCount: 2 },
};

// ── Tests ─────────────────────────────────────────────────────────────────────

import { useDoctor } from "../../../../api/staff";

describe("DoctorPaginaView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("SC-D3D-1: shows loading skeleton", async () => {
    (useDoctor as ReturnType<typeof vi.fn>).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    const { DoctorPaginaView } = await import("./DoctorPaginaView");
    render(<DoctorPaginaView doctorId="doc-1" />, { wrapper });

    // Loading state renders aria-busy container
    expect(document.querySelector('[aria-busy="true"]')).toBeTruthy();
  });

  it("SC-D3D-2: never state shows Generar perfil CTA", async () => {
    (useDoctor as ReturnType<typeof vi.fn>).mockReturnValue({
      data: baseDoctorNeverGenerated,
      isLoading: false,
      isError: false,
    });

    const { DoctorPaginaView } = await import("./DoctorPaginaView");
    render(<DoctorPaginaView doctorId="doc-1" />, { wrapper });

    expect(screen.getByRole("button", { name: /generar perfil/i })).toBeTruthy();
  });

  it("SC-D3D-3: quiet state shows Regenerar button", async () => {
    (useDoctor as ReturnType<typeof vi.fn>).mockReturnValue({
      data: doctorQuietState,
      isLoading: false,
      isError: false,
    });

    const { DoctorPaginaView } = await import("./DoctorPaginaView");
    render(<DoctorPaginaView doctorId="doc-1" />, { wrapper });

    expect(screen.getByRole("button", { name: /regenerar/i })).toBeTruthy();
    // Shows last generation date
    expect(screen.getByText(/última generación/i)).toBeTruthy();
  });

  it("SC-D3D-4: material_new state shows ⚡ banner + Actualizar", async () => {
    (useDoctor as ReturnType<typeof vi.fn>).mockReturnValue({
      data: doctorMaterialNew,
      isLoading: false,
      isError: false,
    });

    const { DoctorPaginaView } = await import("./DoctorPaginaView");
    render(<DoctorPaginaView doctorId="doc-1" />, { wrapper });

    expect(screen.getByRole("status", { name: /nuevo material/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /actualizar perfil/i })).toBeTruthy();
  });

  it("SC-D3D-5: never state — clicking CTA calls generate mutation", async () => {
    (useDoctor as ReturnType<typeof vi.fn>).mockReturnValue({
      data: baseDoctorNeverGenerated,
      isLoading: false,
      isError: false,
    });

    const { DoctorPaginaView } = await import("./DoctorPaginaView");
    render(<DoctorPaginaView doctorId="doc-1" />, { wrapper });

    fireEvent.click(screen.getByRole("button", { name: /generar perfil/i }));
    expect(mockMutate).toHaveBeenCalledOnce();
  });

  it("SC-D3D-6: quiet state — clicking Regenerar with profile shows confirm modal", async () => {
    (useDoctor as ReturnType<typeof vi.fn>).mockReturnValue({
      data: doctorQuietState,
      isLoading: false,
      isError: false,
    });

    const { DoctorPaginaView } = await import("./DoctorPaginaView");
    render(<DoctorPaginaView doctorId="doc-1" />, { wrapper });

    fireEvent.click(screen.getByRole("button", { name: /regenerar/i }));
    // Confirm modal should appear
    expect(screen.getByRole("dialog")).toBeTruthy();
    expect(screen.getByText(/reemplazar el perfil actual/i)).toBeTruthy();
  });

  it("SC-D3D-7: error state shows error message", async () => {
    (useDoctor as ReturnType<typeof vi.fn>).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    const { DoctorPaginaView } = await import("./DoctorPaginaView");
    render(<DoctorPaginaView doctorId="doc-1" />, { wrapper });

    expect(screen.getByRole("alert")).toBeTruthy();
  });

  it("SC-D3D-8: PublicLinkBar renders with visibility toggle", async () => {
    (useDoctor as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { ...baseDoctorNeverGenerated, publicSlug: "ana-garcia", clinicSlug: "sonrisas-lima", visibleEnLanding: false },
      isLoading: false,
      isError: false,
    });

    const { DoctorPaginaView } = await import("./DoctorPaginaView");
    render(<DoctorPaginaView doctorId="doc-1" />, { wrapper });

    const linkBar = screen.getByTestId("public-link-bar");
    expect(linkBar).toBeTruthy();
    expect(screen.getByRole("button", { name: /publicar/i })).toBeTruthy();
  });

  it("SC-D3B-pagina-1: BioRepoInputs mounts on Página tab with material-del-doctor section", async () => {
    (useDoctor as ReturnType<typeof vi.fn>).mockReturnValue({
      data: baseDoctorNeverGenerated,
      isLoading: false,
      isError: false,
    });

    const { DoctorPaginaView } = await import("./DoctorPaginaView");
    render(<DoctorPaginaView doctorId="doc-1" />, { wrapper });

    // Section heading "Material del doctor" must be present on Página tab
    expect(screen.getByText(/material del doctor/i)).toBeTruthy();
    // The bio material section container
    expect(screen.getByTestId("bio-material-section")).toBeTruthy();
    // BioRepoInputs renders notes textarea (D3-B lives here, not in Perfil)
    expect(screen.getByLabelText("Notas para la bio")).toBeTruthy();
  });
});
