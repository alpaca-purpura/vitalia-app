// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * AppointmentDrawerStaleBanner.tsx — Stale data warning banner for AppointmentDrawer.
 * T-14 vitalia-fase2-valeria-agenda
 *
 * Rendered when useDrawerStore.staleDetected=true (polling detected a remote update
 * on the currently open appointment). User can trigger manual refetch.
 *
 * SC-6: concurrent users — two staff members editing the same appointment.
 * Polling every 30s detects updated_at mismatch → sets staleDetected=true → banner.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.11 + 06-tickets.yaml T-14
 */

import { AlertTriangle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

// ── Props ─────────────────────────────────────────────────────────────────────

export interface AppointmentDrawerStaleBannerProps {
  /** Callback to trigger manual refetch of appointment detail. */
  onReload: () => void;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Displays warning banner when appointment data was updated remotely.
 * Shows "Recargar" button that invalidates the React Query cache.
 */
export function AppointmentDrawerStaleBanner({
  onReload,
}: AppointmentDrawerStaleBannerProps) {
  return (
    <Alert
      variant="default"
      className="border-[color:var(--vitalia-warning-color)]/50 bg-[color:var(--vitalia-warning-color)]/8"
      role="status"
      aria-live="polite"
      data-testid="stale-banner"
    >
      <AlertTriangle
        className="h-4 w-4 text-[color:var(--vitalia-warning-color)]"
        aria-hidden="true"
      />
      <AlertDescription className="flex items-center justify-between gap-4">
        <span className="text-[color:var(--vitalia-warning-color)]">
          Este turno fue actualizado por otro usuario.
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={onReload}
          className="border-[color:var(--vitalia-warning-color)] text-[color:var(--vitalia-warning-color)] hover:bg-[color:var(--vitalia-warning-color)]/10 shrink-0"
        >
          Recargar datos
        </Button>
      </AlertDescription>
    </Alert>
  );
}
