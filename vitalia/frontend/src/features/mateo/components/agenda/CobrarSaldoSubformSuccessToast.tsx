// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * CobrarSaldoSubformSuccessToast.tsx — Success toast trigger for CobrarSaldoSubform.
 * T-15 vitalia-fase2-valeria-agenda
 *
 * Calls sonner toast.success() with:
 *   - "Cobro {currency} {amount}" message
 *   - Link to fiscal PDF if fiscalDocUrl is present
 *   - Variant: success (green)
 *
 * This is a utility module (not a React component) that wraps sonner toast.
 * Exported as a named function for use in CobrarSaldoSubform onSuccess handler.
 *
 * HIPAA-lite: amount + currency are NOT PHI — safe to show in toast.
 * Spanish neutro LatAm: all user-facing strings.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE utility; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.7 + 01-spec.md A4 + 06-tickets.yaml T-15
 */

import { ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { formatMoney } from "@/lib/format/formatMoney";
import type { ChargeResponseDTO } from "../../types/agenda-schema";

// ── Types ──────────────────────────────────────────────────────────────────

export interface ShowChargeSuccessToastParams {
  /** Response from charge mutation. */
  response: ChargeResponseDTO;
  /** Tenant locale for Intl.NumberFormat (e.g., "es-PE"). */
  tenantLocale: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────

/**
 * Returns human-readable fiscal emission status label.
 */
function getFiscalStatusLabel(
  status: ChargeResponseDTO["fiscalEmissionStatus"],
  docType: string | null | undefined,
): string | null {
  if (status === "emitted" && docType) {
    return `${docType.charAt(0).toUpperCase()}${docType.slice(1)} emitida`;
  }
  if (status === "pending") {
    return "Comprobante en proceso";
  }
  return null;
}

// ── Toast function ─────────────────────────────────────────────────────────

/**
 * Shows a sonner success toast for a completed charge.
 * Call this from CobrarSaldoSubform onSuccess handler.
 */
export function showChargeSuccessToast({
  response,
  tenantLocale,
}: ShowChargeSuccessToastParams): void {
  const amountFormatted = formatMoney(
    response.amountCents / 100,
    response.currency,
    tenantLocale,
  );

  const fiscalLabel = getFiscalStatusLabel(
    response.fiscalEmissionStatus,
    response.fiscalDocId,
  );

  const description = fiscalLabel ?? "Cobro registrado exitosamente";

  // Build toast action if fiscal doc URL available
  const action =
    response.fiscalDocUrl
      ? {
          label: "Ver comprobante",
          onClick: () => {
            window.open(response.fiscalDocUrl!, "_blank", "noopener,noreferrer");
          },
        }
      : undefined;

  toast.success(`Cobro ${amountFormatted} registrado`, {
    description,
    action,
    duration: 6000,
  });
}

// ── JSX description component for rich toast (if needed by sonner) ─────────

export interface ChargeSuccessToastDescriptionProps {
  response: ChargeResponseDTO;
  tenantLocale: string;
}

/**
 * Rich description content for sonner toast with fiscal doc link.
 * Used as the `description` prop for toast.success().
 */
export function ChargeSuccessToastDescription({
  response,
  tenantLocale: _tenantLocale,
}: ChargeSuccessToastDescriptionProps) {
  const fiscalLabel = getFiscalStatusLabel(
    response.fiscalEmissionStatus,
    response.fiscalDocId,
  );

  return (
    <span className="flex flex-col gap-1 text-sm">
      <span>{fiscalLabel ?? "Cobro registrado exitosamente"}</span>
      {response.fiscalDocUrl && (
        <a
          href={response.fiscalDocUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-xs text-[color:var(--vitalia-success-color)] hover:underline underline-offset-2"
          aria-label="Ver comprobante fiscal (nueva pestaña)"
        >
          <ExternalLink className="h-3 w-3" aria-hidden="true" />
          Ver comprobante
        </a>
      )}
    </span>
  );
}
