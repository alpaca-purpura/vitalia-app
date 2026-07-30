// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
"use client";
/**
 * ResponsibleView.tsx — DPO/data-protection reference (read-only tab).
 *
 * Shows tenant DPO info fetched from /api/v1/clinics/account/dpo/.
 * Provides link to Configuración > Seguridad for editing DPO.
 *
 * Read-only: no PATCH / no autosave on this tab.
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: 03-arch.md § 5 (DpoReferenceDTO) + § 10
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { PageContentStack } from "@luana/ui-kit";
import { cuentaKeys, getDpoReference } from "../../api/get-account";
import type { DpoReferenceDTO } from "../../types/cuenta.types";

export interface ResponsibleViewProps {
  tenantId: string;
  /** Clerk org / tenant slug — used to build navigation href for seguridad tab. */
  tenantSlug?: string;
  /**
   * Optional initial DPO data — SSR hydration or test override.
   * When provided, used as placeholder until React Query resolves.
   */
  dpoData?: DpoReferenceDTO;
  className?: string;
}

// ── Skeleton ──────────────────────────────────────────────────────────────────

function DpoSkeleton() {
  return (
    <div aria-busy="true" aria-label="Cargando responsable" className="flex flex-col gap-4">
      <Skeleton className="h-3 w-[40%] rounded" />
      <Skeleton className="h-3 w-[60%] rounded" />
      <Skeleton className="h-3 w-[30%] rounded" />
    </div>
  );
}

// ── DPO detail card ───────────────────────────────────────────────────────────

function DpoCard({
  dpo,
  seguridadHref,
}: {
  dpo: DpoReferenceDTO;
  seguridadHref: string;
}) {
  const hasData = !!dpo.name || !!dpo.email;

  return (
    <PageContentStack>
      <p className="text-sm text-muted-foreground">
        El responsable del tratamiento de datos ({dpo.roleLabel}) es quien responde
        ante los pacientes por el uso de su información.
      </p>

      {hasData ? (
        <dl className="rounded-lg border bg-card p-4 space-y-2">
          {dpo.name && (
            <div className="flex items-baseline gap-2">
              <dt className="text-xs text-muted-foreground w-24 shrink-0">Nombre</dt>
              <dd className="text-sm font-medium">{dpo.name}</dd>
            </div>
          )}
          {dpo.email && (
            <div className="flex items-baseline gap-2">
              <dt className="text-xs text-muted-foreground w-24 shrink-0">Correo</dt>
              <dd className="text-sm font-medium">{dpo.email}</dd>
            </div>
          )}
          <div className="flex items-baseline gap-2">
            <dt className="text-xs text-muted-foreground w-24 shrink-0">Rol</dt>
            <dd className="text-sm">{dpo.roleLabel}</dd>
          </div>
        </dl>
      ) : (
        <div
          className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground"
          data-testid="dpo-empty-state"
        >
          Aún no has configurado un responsable de datos.
        </div>
      )}

      <p className="text-sm text-muted-foreground">
        Para editar esta información, ve a{" "}
        <Link
          href={seguridadHref}
          className="font-medium text-primary underline underline-offset-2 hover:text-primary/80 transition-colors"
        >
          Configuración &gt; Seguridad
        </Link>
        .
      </p>
    </PageContentStack>
  );
}

// ── Error banner ──────────────────────────────────────────────────────────────

function ErrorBanner() {
  return (
    <div
      role="alert"
      className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive"
    >
      No se pudo cargar la información del responsable.
    </div>
  );
}

// ── ResponsibleView ───────────────────────────────────────────────────────────

/**
 * ResponsibleView — DPO reference read-only tab for config/cuenta/responsable.
 */
export function ResponsibleView({
  tenantId,
  tenantSlug,
  dpoData: initialDpoData,
  className,
}: ResponsibleViewProps) {
  const { getToken, isLoaded, isSignedIn, userId } = useAuth();

  const {
    data: fetchedDpo,
    isLoading,
    isError,
  } = useQuery<DpoReferenceDTO>({
    queryKey: cuentaKeys.dpo(tenantId),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !userId) throw new Error("No autenticado");
      return getDpoReference({ token, tenantId, userId });
    },
    enabled: isLoaded && !!isSignedIn && !!userId,
    // Use initialDpoData as placeholder data for SSR hydration / test overrides
    initialData: initialDpoData,
  });

  // Prefer fetched data; fall back to initialDpoData
  const dpo = fetchedDpo ?? initialDpoData;

  // Build seguridad href — uses manageUrlSubpath from DPO response if available
  const slug = tenantSlug ?? tenantId;
  const seguridadHref = dpo?.manageUrlSubpath
    ? `/${slug}/${dpo.manageUrlSubpath}`
    : `/${slug}/config/seguridad`;

  return (
    <PageContentStack
      className={cn("p-6", className)}
      data-testid="responsible-view"
    >
      <div>
        <h1 className="text-base font-semibold text-foreground">
          Responsable del tratamiento de datos
        </h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Quién es el responsable legal (DPO) de los datos de pacientes de tu clínica.
        </p>
      </div>

      {isLoading ? (
        <DpoSkeleton />
      ) : isError ? (
        <ErrorBanner />
      ) : dpo ? (
        <DpoCard dpo={dpo} seguridadHref={seguridadHref} />
      ) : (
        <p className="text-sm text-muted-foreground">
          No hay información disponible.
        </p>
      )}
    </PageContentStack>
  );
}

ResponsibleView.displayName = "ResponsibleView";
