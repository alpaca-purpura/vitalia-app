// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
"use client";
/**
 * StaffWorkspaceShell.tsx — Staff workspace layout wrapper.
 *
 * Renders:
 *   1. EntityWorkspaceLayout (@luana/ui-kit) — N3 canon ribbon + content slot
 *   2. EntityPicker via entityIdentitySlot (canon §6.3 — "cambiar sin volver",
 *      D3-A switcher: change doctor WITHOUT going back to the directory,
 *      PRESERVING the current leaf)
 *   3. Children slot — perfil/horarios/servicios page content
 *
 * Builds leaf hrefs relative to doctor workspace.
 * activeLeaf passed explicitly (vitalia uses static leaf segments, not [leaf] param).
 *
 * Per ADR-vitalia-004 § 3: Client Component (needs usePathname for active leaf).
 * MIGRATED to @luana/ui-kit EntityWorkspaceLayout (vitalia-shell-core-hardening T-5).
 *
 * T-FE-2 + T-FE-switcher-wire vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § FSD-Lite + § EntitySubNavBar + 03-arch-delta.md § 2.2
 * downstream-regression-na: brand-local vitalia feature component
 */

import { useCallback, useMemo } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { EntityWorkspaceLayout, EntityPicker } from "@luana/ui-kit";
import type { EntitySubNavLeaf, EntityPickerItem } from "@luana/ui-kit";
import {
  staffKeys,
  useStaffActorHeaders,
  useDoctorPickerSearchFn,
} from "../../../api/staff";
import { fetchClient } from "@/lib/api/fetchClient";
import { useClinicId } from "@/hooks/useClinicId";
import { useTenantId } from "@/hooks/useTenantId";
import type { DoctorDetail } from "../../../types/staff.types";

// Client component: SAME-ORIGIN relative base (tunnel/reverse-proxy routes /api/* → BE).
// Absolute http://localhost:8002 cross-origins the browser → CORS block. See staff.ts note
// + regression 2026-06-06 (staff workspace refetch CORS-broken; masked by SSR initialData).
const API_BASE = "";

interface StaffWorkspaceShellProps {
  tenantId: string;
  doctorId: string;
  initialDoctor?: DoctorDetail;
  children: React.ReactNode;
}

const LEAF_DEFS = [
  { id: "perfil", label: "Perfil" },
  { id: "horarios", label: "Horarios" },
  { id: "servicios", label: "Servicios" },
  { id: "pagina", label: "Página" },
] as const;

/**
 * Extracts the active leaf from the URL pathname.
 * Pattern: /{tenantId}/lisa/staff/{doctorId}/{leaf}
 * Used as activeLeaf override since vitalia uses static leaf segments (not [leaf] param).
 */
function extractLeafFromPath(pathname: string | null): string | null {
  if (!pathname) return null;
  const segments = pathname.split("/").filter(Boolean);
  // [0]=tenantId, [1]=lisa, [2]=staff, [3]=doctorId, [4]=leaf
  return segments[4] ?? null;
}

/**
 * Known workspace leaves for leaf-preserving navigation. Includes "pagina"
 * (4th leaf, D3-D) so the switcher keeps working when that leaf lands —
 * the leaf itself is NOT added here (T-FE-pagina-publica owns LEAF_DEFS).
 */
const PRESERVABLE_LEAVES = new Set(["perfil", "horarios", "servicios", "pagina"]);

/**
 * buildDoctorWorkspaceHref — pure leaf-preserving navigation target (D3-A).
 *
 * Derives the CURRENT leaf from the pathname and rebuilds the workspace URL
 * for the picked doctor: /{tenantId}/lisa/staff/{doctorId}/{currentLeaf}.
 * Unknown/missing leaf → "perfil" (workspace default).
 *
 * Ratified by Chris: switching doctor PRESERVES the active leaf (SC-D3A-1:
 * Horarios de Ana → Horarios de Carlos).
 */
export function buildDoctorWorkspaceHref(
  tenantId: string,
  doctorId: string,
  pathname: string | null,
): string {
  const leaf = extractLeafFromPath(pathname);
  const targetLeaf = leaf && PRESERVABLE_LEAVES.has(leaf) ? leaf : "perfil";
  return `/${tenantId}/lisa/staff/${doctorId}/${targetLeaf}`;
}

export function StaffWorkspaceShell({
  tenantId,
  doctorId,
  initialDoctor,
  children,
}: StaffWorkspaceShellProps) {
  const pathname = usePathname();
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const clinicId = useClinicId();
  // tenantId from useTenantId() for API calls (UUID from publicMetadata.tenant_id).
  // The prop tenantId is used for URL routing only — may differ from the API tenant UUID.
  const apiTenantId = useTenantId();
  // GET /{id} (detail) requires X-User-ID (UUID) — audit-on-PHI-read. Without it → 422
  // ("No se pudo cargar el perfil", bug #5). Same key as useDoctor → keep headers consistent.
  const actorHeaders = useStaffActorHeaders();

  // Build leaf hrefs
  const leaves: EntitySubNavLeaf[] = LEAF_DEFS.map((def) => ({
    id: def.id,
    label: def.label,
    href: `/${tenantId}/lisa/staff/${doctorId}/${def.id}`,
  }));

  // Vitalia uses static leaf segments (/perfil, /horarios, /servicios) — not [leaf] dynamic
  // param. Pass explicitly as override so EntityWorkspaceLayout resolves the active tab.
  const activeLeaf = extractLeafFromPath(pathname);

  // Hydrate doctor detail (SSR initialData from layout)
  const { data: doctor, isLoading: isDoctorLoading } = useQuery({
    queryKey: staffKeys.detail(doctorId),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !apiTenantId) throw new Error("Sin autenticación");
      return fetchClient<DoctorDetail>(
        `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}`,
        { token, tenantId: apiTenantId, clinicId, headers: actorHeaders },
      );
    },
    // Gate until X-User-ID (from /me) is ready — see useDoctor (bug #5 race).
    enabled: isLoaded && !!isSignedIn && !!actorHeaders["X-User-ID"],
    initialData: initialDoctor,
    staleTime: 30_000,
  });

  // Memoized: `doctor` (React Query data) is referentially stable between
  // renders unless the data changes → entity (and the slot below) stay stable.
  const entity = useMemo(
    () =>
      doctor
        ? {
            id: doctor.id,
            name: `${doctor.firstName} ${doctor.lastName}`,
            avatarUrl: doctor.avatarUrl ?? null,
          }
        : null,
    [doctor],
  );

  // ── D3-A entity switcher (canon §6.3 — EntityPicker in the identity slot) ──
  const router = useRouter();
  const pickerSearchFn = useDoctorPickerSearchFn();

  // Navigate to the picked doctor PRESERVING the current leaf (SC-D3A-1).
  // Same doctor → no-op (no redundant navigation).
  const onPickDoctor = useCallback(
    (picked: EntityPickerItem) => {
      if (picked.id === doctorId) return;
      router.push(buildDoctorWorkspaceHref(tenantId, picked.id, pathname));
    },
    [doctorId, tenantId, pathname, router],
  );

  // Memoized slot node (stable unless inputs change — avoids re-creating the
  // picker subtree on unrelated shell re-renders).
  const entityIdentitySlot = useMemo(
    () =>
      entity ? (
        <EntityPicker
          value={entity}
          searchFn={pickerSearchFn}
          onChange={onPickDoctor}
          searchPlaceholder="Buscar integrante…"
          testId="doctor-picker"
        />
      ) : undefined,
    [entity, pickerSearchFn, onPickDoctor],
  );

  return (
    <EntityWorkspaceLayout
      rootHref={`/${tenantId}/lisa/staff`}
      rootLabel="Staff"
      entity={entity}
      leaves={leaves}
      activeLeaf={activeLeaf}
      isLoading={isDoctorLoading && !initialDoctor}
      entityIdentitySlot={entityIdentitySlot}
    >
      {children}
    </EntityWorkspaceLayout>
  );
}
