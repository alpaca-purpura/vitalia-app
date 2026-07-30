// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * StaffErrorBanner.tsx — Error banner + Reintentar for Staff directory (SC-7).
 *
 * Shown when GET /doctors responds 503/timeout.
 * Provides accessible error feedback + retry action.
 * Never blank screen, never infinite spinner.
 *
 * Microcopy per 01-spec.md § Microcopy (authoritative).
 * Spanish neutro LatAm — sin voseo.
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § SC-7 + § Estados visuales + § Microcopy
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";

interface StaffErrorBannerProps {
  onRetry: () => void;
}

/**
 * StaffErrorBanner — renders when staff list fetch fails.
 * data-testid="error-banner-staff" for Playwright selectors.
 */
export function StaffErrorBanner({ onRetry }: StaffErrorBannerProps) {
  return (
    <div
      role="alert"
      data-testid="error-banner-staff"
      className="flex flex-col items-center justify-center gap-4 py-16 px-6 text-center"
    >
      <div className="flex items-center gap-2 text-destructive">
        <AlertCircle className="h-6 w-6" aria-hidden="true" />
        <span className="font-medium">No pudimos cargar el equipo.</span>
      </div>

      <p className="text-sm text-muted-foreground">
        Comprueba tu conexión e intenta de nuevo.
      </p>

      <Button
        variant="outline"
        onClick={onRetry}
        data-testid="btn-reintentar"
        aria-label="Reintentar cargar el equipo"
      >
        Reintentar
      </Button>
    </div>
  );
}
