// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * AppointmentDrawerHeader.tsx — Header section of the AppointmentDrawer.
 * T-14 vitalia-fase2-valeria-agenda
 *
 * Renders:
 *   - Avatar with patient initials (PHI-safe — uses masked name initial)
 *   - PHI-masked patient name ("P. Hernández" — server-masked)
 *   - PHI-masked DNI ("12.***.***" — server-masked, null if not registered)
 *   - "Ver ficha completa" disabled button + Tooltip "Próximamente" (Q7 cement)
 *
 * HIPAA-lite constraint: this component ONLY renders masked strings from BE.
 * FE never receives raw PHI. PiiMaskedSpan further confirms display-only masking.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.6 + 06-tickets.yaml T-14
 */

import { User } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

// ── Props ─────────────────────────────────────────────────────────────────────

export interface AppointmentDrawerHeaderProps {
  /**
   * PHI-masked patient name. Format: "P. Hernández"
   * Always a masked string from the server — never raw PHI.
   */
  patientNameMasked: string;
  /**
   * PHI-masked DNI. Format: "12.***.***"
   * Null if not registered on patient record.
   */
  patientDniMasked: string | null;
  /** Additional CSS classes. */
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Drawer header with patient identity (PHI-masked) + quick navigation.
 *
 * "Ver ficha completa" links to F2-S2 (pacientes module) — disabled
 * until that story is done (Q7 cement: disabled + tooltip "Próximamente").
 */
export function AppointmentDrawerHeader({
  patientNameMasked,
  patientDniMasked,
  className,
}: AppointmentDrawerHeaderProps) {
  // Derive avatar initial from masked name (safe: first char of masked string).
  // Guard against a missing/empty masked name — a missing field must never crash the
  // whole agenda via the error boundary (D9 follow-on, story vitalia-scheduling-mateo-review).
  const avatarInitial = (patientNameMasked ?? "").charAt(0).toUpperCase();

  return (
    <div
      className={cn("flex items-center gap-3 px-6 py-4", className)}
      id="drawer-title"
    >
      {/* Avatar — initial from PHI-masked name (no raw PHI) */}
      <div
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-full",
          "bg-agent-valeria/20 text-agent-valeria font-semibold text-sm",
        )}
        aria-hidden="true"
      >
        {avatarInitial || <User className="h-5 w-5" />}
      </div>

      {/* Patient identity (PHI-masked server-side) */}
      <div className="flex flex-col gap-0.5 min-w-0 flex-1">
        <span
          className="font-semibold text-sm text-foreground truncate"
          data-phi
          data-phi-type="name"
          aria-label={`Paciente: ${patientNameMasked}`}
        >
          {patientNameMasked}
        </span>
        {patientDniMasked && (
          <span
            className="text-xs text-muted-foreground font-mono"
            data-phi
            data-phi-type="dni"
            aria-label={`DNI: ${patientDniMasked}`}
          >
            {patientDniMasked}
          </span>
        )}
      </div>

      {/* "Ver ficha completa" — disabled, links to F2-S2 when done (Q7 cement) */}
      <Tooltip>
        <TooltipTrigger asChild>
          {/* Wrapper span needed: disabled button doesn't fire tooltip events */}
          <span className="shrink-0">
            <Button
              variant="outline"
              size="sm"
              disabled
              aria-disabled="true"
              aria-describedby="ver-ficha-tooltip"
              className="cursor-not-allowed opacity-50"
            >
              Ver ficha completa
            </Button>
          </span>
        </TooltipTrigger>
        <TooltipContent id="ver-ficha-tooltip" side="bottom">
          Pacientes — próximamente disponible en Fase 2
        </TooltipContent>
      </Tooltip>
    </div>
  );
}
