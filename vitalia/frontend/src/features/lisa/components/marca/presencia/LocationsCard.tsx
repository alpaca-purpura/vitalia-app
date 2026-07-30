// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * LocationsCard.tsx — Read-only display of clinic locations (sedes).
 *
 * Data source: GET /lisa/marca/locations (read-only from clinics module).
 * Each location row shows: name, address, Editar button (disabled — future story).
 * "+ Agregar sede" button is disabled (future story).
 *
 * No autosave — this is read-only data from the clinics module.
 * Edit/Add flows are deferred to a future story.
 *
 * Spanish neutro LatAm — no voseo.
 *
 * T-7 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-7 + mockups/presencia-section.html § locations
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { marcaKeys } from "../../../api/marca";
import { getLocations } from "../../../api/marca-presence-api";
import type { LocationItem } from "../../../api/marca-presence-api";

// ── Types ──────────────────────────────────────────────────────────────────────

export interface LocationsCardProps {
  tenantId: string;
  clinicId?: string | null;
  className?: string;
}

// ── LocationRow ────────────────────────────────────────────────────────────────

interface LocationRowProps {
  location: LocationItem;
}

function LocationRow({ location }: LocationRowProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-3 rounded-md",
        "bg-muted/40 px-3 py-2.5",
      )}
    >
      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
        <span className="truncate text-sm font-medium text-foreground">
          {location.name}
        </span>
        <span className="truncate text-xs text-muted-foreground">{location.address}</span>
      </div>

      {/* Editar — disabled (future story) */}
      <Button
        type="button"
        variant="ghost"
        size="sm"
        disabled
        aria-disabled="true"
        aria-label={`Editar sede ${location.name} (próximamente)`}
        className="shrink-0 text-xs text-muted-foreground"
      >
        Editar
      </Button>
    </div>
  );
}

// ── LocationsCard ──────────────────────────────────────────────────────────────

/**
 * LocationsCard — displays clinic sedes from the clinics module (read-only).
 * Edit and Add are deferred to future stories.
 */
export function LocationsCard({ tenantId, clinicId, className }: LocationsCardProps) {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  const {
    data,
    isLoading,
    isError,
  } = useQuery({
    queryKey: marcaKeys.locations(tenantId),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return getLocations({ token, tenantId, clinicId });
    },
    enabled: isLoaded && !!isSignedIn,
  });

  const locations = data?.items ?? [];

  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-card p-4 shadow-sm",
        className,
      )}
    >
      <div className="flex flex-col gap-3">
        {/* Card header */}
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground">Ubicaciones</h3>
          <span className="text-xs text-muted-foreground">
            {locations.length > 0 ? `${locations.length} sede${locations.length === 1 ? "" : "s"}` : null}
          </span>
        </div>

        {/* Location list */}
        {isLoading ? (
          <div className="flex flex-col gap-2" aria-busy="true" aria-label="Cargando ubicaciones">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-14 w-full rounded-md" />
            ))}
          </div>
        ) : isError ? (
          <div role="alert">
            <p className="text-sm text-destructive">
              No se pudieron cargar las ubicaciones. Intenta de nuevo.
            </p>
          </div>
        ) : locations.length === 0 ? (
          <div className="rounded-md border border-dashed border-border/60 bg-muted/20 p-4 text-center">
            <p className="text-sm text-muted-foreground">Aún no hay sedes registradas.</p>
          </div>
        ) : (
          <div
            className="flex flex-col gap-2"
            role="list"
            aria-label="Lista de sedes"
          >
            {locations.map((loc) => (
              <div key={loc.id} role="listitem">
                <LocationRow location={loc} />
              </div>
            ))}
          </div>
        )}

        {/* + Agregar sede — disabled (future story) */}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled
          aria-disabled="true"
          aria-label="Agregar sede (próximamente)"
          className="w-fit text-xs text-muted-foreground"
        >
          <svg
            aria-hidden="true"
            className="mr-1 h-3.5 w-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Agregar sede
        </Button>
      </div>
    </div>
  );
}

LocationsCard.displayName = "LocationsCard";
