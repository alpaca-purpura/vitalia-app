// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * PresenciaView.tsx — Client root for Presencia sub-sub-tab.
 *
 * ADR-vitalia-004 v1.1 — N3-static routing pattern.
 * "use client" root per ADR § 3. Props hydrated from Server Component page.tsx.
 *
 * Composition (in render order):
 *   1. Section header + AutosaveBadge
 *   2. WebsiteCard                — URL input + conn-status
 *   3. SocialMediaLinksEditor     — 5 social rows
 *   4. TrustSignalsEditor         — OQ-D hybrid catalog
 *   5. LocationsCard              — read-only sedes from clinics module
 *
 * (Bug #5 vitalia-bugfix-shell-nav-scroll-errors T-5: se removió el banner
 *  "Editor de landing pública — próximamente" — InfoBannerLandingDescoped. El
 *  editor de landing NO se construye acá; eso es otra story.)
 *
 * Data layer:
 *   - useQuery contact            — GET /lisa/marca/contact
 *   - useContactAutosave          — PUT /lisa/marca/contact (debounce 600ms)
 *   - TrustSignalsEditor manages its own queries/mutations internally
 *   - LocationsCard manages its own query internally
 *
 * React Query key: marcaKeys.contact(tenantId) = ['lisa','marca','contact', tenantId]
 *
 * HIPAA-lite: fetchClient auto-injects X-Tenant-ID + X-Clinic-ID.
 * PHI never in URL/searchParams. All mutations via PUT body.
 *
 * T-7 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-7 + ADR-vitalia-004 § 3 + mockups/presencia-section.html
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { FloatingAutosaveIndicator } from "@/components/shared/FloatingAutosaveIndicator";
import { marcaKeys } from "../../../api/marca";
import { getContact } from "../../../api/marca-presence-api";
import { useContactAutosave } from "../../../hooks/useContactAutosave";
import { WebsiteCard } from "./WebsiteCard";
import { SocialMediaLinksEditor } from "./SocialMediaLinksEditor";
import { TrustSignalsEditor } from "./TrustSignalsEditor";
import { LocationsCard } from "./LocationsCard";
import type { ContactPatchPayload } from "../../../hooks/useContactAutosave";

// ── Types ──────────────────────────────────────────────────────────────────────

export interface PresenciaViewProps {
  /** Clerk org ID — used for X-Tenant-ID and React Query keys. */
  tenantId: string;
  /**
   * Clinic ID for HIPAA-lite dual filter.
   * Passed from page.tsx Server Component.
   */
  clinicId?: string | null;
  className?: string;
}

// ── Loading skeleton ───────────────────────────────────────────────────────────

function PresenciaLoadingSkeleton() {
  return (
    <div
      aria-busy="true"
      aria-label="Cargando sección Presencia"
      className="flex flex-col gap-4"
    >
      <Skeleton className="h-4 w-[40%]" />
      <Skeleton className="h-[60px] w-full rounded-lg" />
      <Skeleton className="h-[80px] w-full rounded-lg" />
      <Skeleton className="h-[200px] w-full rounded-lg" />
      <Skeleton className="h-[220px] w-full rounded-lg" />
      <Skeleton className="h-[100px] w-full rounded-lg" />
    </div>
  );
}

// ── PresenciaView ──────────────────────────────────────────────────────────────

/**
 * PresenciaView — "use client" root for the Presencia sub-sub-tab.
 * Composes all presencia cards and wires the contact autosave hook.
 */
export function PresenciaView({ tenantId, clinicId, className }: PresenciaViewProps) {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  // ── React Query: fetch contact data ─────────────────────────────────────
  const {
    data: contact,
    isLoading: isContactLoading,
    isError: isContactError,
  } = useQuery({
    queryKey: marcaKeys.contact(tenantId),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return getContact({ token, tenantId, clinicId });
    },
    enabled: isLoaded && !!isSignedIn,
  });

  // ── Autosave hook ────────────────────────────────────────────────────────
  const { autosaveStatus, savedAt, scheduleAutosave } = useContactAutosave({
    tenantId,
    clinicId,
  });

  // ── Handler passed to children ───────────────────────────────────────────
  const handleScheduleAutosave = useCallback(
    (values: ContactPatchPayload) => {
      scheduleAutosave(values);
    },
    [scheduleAutosave],
  );

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div data-testid="presencia-view" className={cn("flex flex-col gap-6 p-6", className)}>
      {/* Loading state */}
      {isContactLoading && <PresenciaLoadingSkeleton />}

      {/* Error state */}
      {isContactError && !isContactLoading && (
        <div role="alert" className="rounded-lg border border-destructive/30 bg-destructive/10 p-4">
          <p className="text-sm text-destructive">
            No se pudo cargar la información de presencia. Recarga la página e intenta de nuevo.
          </p>
        </div>
      )}

      {/* Content — rendered once data loads (skeleton hides it) */}
      {!isContactLoading && (
        <div className="flex flex-col gap-4">
          {/* 1. Website URL */}
          <WebsiteCard
            websiteUrl={contact?.websiteUrl}
            onScheduleAutosave={handleScheduleAutosave}
          />

          {/* 2. Social media links */}
          <SocialMediaLinksEditor
            instagram={contact?.instagramHandle}
            tiktok={contact?.tiktokHandle}
            facebook={contact?.facebookPage}
            googleBusiness={contact?.googleBusinessUrl}
            onScheduleAutosave={handleScheduleAutosave}
          />

          {/* 3. Trust signals (OQ-D hybrid catalog) */}
          <TrustSignalsEditor
            tenantId={tenantId}
            clinicId={clinicId}
            onScheduleAutosave={handleScheduleAutosave}
          />

          {/* 4. Locations (read-only from clinics module) */}
          <LocationsCard
            tenantId={tenantId}
            clinicId={clinicId}
          />
        </div>
      )}

      <FloatingAutosaveIndicator status={autosaveStatus} savedAt={savedAt} />
    </div>
  );
}

PresenciaView.displayName = "PresenciaView";
