// cap: iam.iam-scaffold-slice-1
// story-origin: vitalia-iam-slice2-phi-real-auth
/**
 * useCurrentUser.test.tsx — TDD RED → GREEN
 *
 * T-3 vitalia-iam-slice2-phi-real-auth
 *
 * Verifica que useCurrentUser lee el rol desde GET /api/v1/iam/users/me
 * (React Query, rol desde DB) y NO desde Clerk publicMetadata.role.
 *
 * Tests:
 * 1. success — rol viene de /me response (no de Clerk metadata)
 * 2. loading — isLoaded false mientras query pending
 * 3. error — /me falla → role null, hasPhiAccess false
 * 4. hasPhiAccess true cuando role es doctor (PHI rol)
 * 5. hasPhiAccess false cuando role es marketing (no PHI)
 * 6. shape CurrentUser intacto (consumers RequireRole/usePiiRoleGate sin cambios)
 */

import React from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import type { ReactNode } from "react";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Mock @clerk/nextjs — no queremos JWKS real en tests unitarios
vi.mock("@clerk/nextjs", () => ({
  useAuth: vi.fn(),
  useUser: vi.fn(),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


// Mock fetchClient — intercepta la llamada a /api/v1/iam/users/me
vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    constructor(response: { status: number; statusText: string }) {
      super(`API error ${response.status}: ${response.statusText}`);
      this.name = "ApiError";
      this.status = response.status;
    }
  },
}));

import { useAuth, useUser } from "@clerk/nextjs";
import { fetchClient } from "@/lib/api/fetchClient";
import { useCurrentUser } from "../useCurrentUser";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Respuesta canónica del engine GET /api/v1/iam/users/me */
interface MeResponse {
  id: string;
  full_name: string | null;
  email: string;
  role: string;
  tenant_id: string | null;
  is_active: boolean;
}

const MOCK_ME_DOCTOR: MeResponse = {
  id: "f1a2b3c4-0000-0000-0000-000000000001",
  full_name: "Doctor Demo",
  email: "doctor.demo@sanare.pe",
  role: "doctor",
  tenant_id: "e69a691d-070e-5caf-a053-6e74642ec100",
  is_active: true,
};

const MOCK_ME_MARKETING: MeResponse = {
  id: "f1a2b3c4-0000-0000-0000-000000000002",
  full_name: "Marketing Demo",
  email: "marketing.demo@sanare.pe",
  role: "marketing",
  tenant_id: "e69a691d-070e-5caf-a053-6e74642ec100",
  is_active: true,
};

function createWrapper(): ({ children }: { children: ReactNode }) => React.ReactElement {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,  // no retry en tests — fallo inmediato
        gcTime: 0,
      },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }): React.ReactElement {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

// ---------------------------------------------------------------------------
// Setup por defecto: Clerk loaded + signed in
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks();

  // Clerk auth: cargado, firmado, token disponible, orgId = tenant Sanaré
  vi.mocked(useAuth).mockReturnValue({
    isLoaded: true,
    isSignedIn: true,
    getToken: vi.fn().mockResolvedValue("test-jwt-token"),
    userId: "user_3EQJjxsvxiZ5exQjucSB651xnUd",
    orgId: "e69a691d-070e-5caf-a053-6e74642ec100",
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } as any);

  // useUser: loaded + user con org (tenant)
  vi.mocked(useUser).mockReturnValue({
    isLoaded: true,
    isSignedIn: true,
    user: {
      id: "user_3EQJjxsvxiZ5exQjucSB651xnUd",
      firstName: "Doctor",
      lastName: "Demo",
      primaryEmailAddress: { emailAddress: "doctor.demo@sanare.pe" },
      // ★ publicMetadata deliberadamente con rol DISTINTO
      // para verificar que useCurrentUser lo ignora post-Slice-2
      publicMetadata: { role: "patient" },
      organizationMemberships: [
        {
          organization: { id: "e69a691d-070e-5caf-a053-6e74642ec100" },
        },
      ],
    },
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } as any);
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useCurrentUser", () => {
  // ── Test 1: success — rol viene de /me, NO de Clerk publicMetadata ────────

  it("devuelve rol desde GET /api/v1/iam/users/me (no desde Clerk publicMetadata)", async () => {
    vi.mocked(fetchClient).mockResolvedValueOnce(MOCK_ME_DOCTOR);

    const { result } = renderHook(() => useCurrentUser(), {
      wrapper: createWrapper(),
    });

    // Espera a que la query resuelva
    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    // ★ El rol debe ser "doctor" (de /me), NO "patient" (de Clerk publicMetadata)
    expect(result.current.role).toBe("doctor");
    expect(result.current.email).toBe("doctor.demo@sanare.pe");

    // fetchClient debió llamarse con la ruta /me correcta
    expect(fetchClient).toHaveBeenCalledWith(
      "/api/v1/iam/users/me",
      expect.objectContaining({
        token: "test-jwt-token",
        tenantId: expect.any(String),
      }),
    );
  });

  // ── Test 2: loading — isLoaded false mientras query pending ───────────────

  it("retorna isLoaded false mientras la query de /me está pendiente", () => {
    // fetchClient nunca resuelve (pendiente)
    vi.mocked(fetchClient).mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useCurrentUser(), {
      wrapper: createWrapper(),
    });

    // Durante el loading, el hook debe indicar que no está cargado
    expect(result.current.isLoaded).toBe(false);
    expect(result.current.role).toBeNull();
    expect(result.current.hasPhiAccess).toBe(false);
  });

  // ── Test 3: error — /me falla → role null, hasPhiAccess false ─────────────

  it("nunca devuelve un rol cuando GET /me falla (no hay data leak)", async () => {
    // fetchClient rechaza inmediatamente — no data de /me
    vi.mocked(fetchClient).mockRejectedValue(
      new Error("Network error"),
    );

    const { result } = renderHook(() => useCurrentUser(), {
      wrapper: createWrapper(),
    });

    // Esperar a que fetchClient haya sido llamado al menos una vez
    await waitFor(() => {
      expect(fetchClient).toHaveBeenCalled();
    });

    // En cualquier estado (loading o error): sin datos de /me → role null, no PHI
    // El hook NO debe devolver un rol inventado ante fallo del endpoint
    expect(result.current.role).toBeNull();
    expect(result.current.hasPhiAccess).toBe(false);
  });

  // ── Test 4: hasPhiAccess true cuando role es doctor ───────────────────────

  it("hasPhiAccess es true cuando el rol es doctor (rol PHI)", async () => {
    vi.mocked(fetchClient).mockResolvedValueOnce(MOCK_ME_DOCTOR);

    const { result } = renderHook(() => useCurrentUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    expect(result.current.role).toBe("doctor");
    expect(result.current.hasPhiAccess).toBe(true);
  });

  // ── Test 5: hasPhiAccess false cuando role es marketing ──────────────────

  it("hasPhiAccess es false cuando el rol es marketing (no PHI)", async () => {
    vi.mocked(fetchClient).mockResolvedValueOnce(MOCK_ME_MARKETING);

    const { result } = renderHook(() => useCurrentUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    expect(result.current.role).toBe("marketing");
    expect(result.current.hasPhiAccess).toBe(false);
  });

  // ── Test 6: shape CurrentUser intacto (consumers sin cambios) ─────────────

  it("retorna shape CurrentUser completo (id, firstName, lastName, email, role, hasPhiAccess, isLoaded)", async () => {
    vi.mocked(fetchClient).mockResolvedValueOnce(MOCK_ME_DOCTOR);

    const { result } = renderHook(() => useCurrentUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoaded).toBe(true);
    });

    // Verificar shape completo — consumers RequireRole/usePiiRoleGate leen todos estos campos
    const cu = result.current;
    expect(cu).toHaveProperty("id");
    expect(cu).toHaveProperty("firstName");
    expect(cu).toHaveProperty("lastName");
    expect(cu).toHaveProperty("email");
    expect(cu).toHaveProperty("role");
    expect(cu).toHaveProperty("hasPhiAccess");
    expect(cu).toHaveProperty("isLoaded");

    // El id debe venir de Clerk (usuario autenticado), no de /me
    expect(typeof cu.id).toBe("string");
    expect(cu.isLoaded).toBe(true);
  });
});
