// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * CobrarSaldoSubformErrorAlert.tsx — Error/Warning alert for CobrarSaldoSubform saga.
 * T-15 vitalia-fase2-valeria-agenda
 *
 * Renders different alert variants depending on error type:
 *   - payment_failed (503): destructive alert + "Reintentar" (same idempotencyKey)
 *   - fiscal_failed (503 post-charge): warning alert + "Reintentar emisión" standalone
 *   - conflict_409: default alert "saldo ya cobrado" + "Entendido" dismiss
 *   - validation_422: destructive alert with field message
 *   - server_error (500): destructive alert generic
 *
 * HIPAA-lite: error messages contain NO PHI (amounts are NOT PHI, no patient data).
 * Spanish neutro LatAm: all user-facing strings.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.7 + 01-spec.md A5/A6/A7 + 06-tickets.yaml T-15
 */

import { AlertTriangle, XCircle, Info, RefreshCw, CheckCircle2 } from "lucide-react";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ChargeErrorState } from "./CobrarSaldoSubform";

// ── Props ──────────────────────────────────────────────────────────────────

export interface CobrarSaldoSubformErrorAlertProps {
  /** Error state from charge saga. */
  errorState: ChargeErrorState;
  /** Retry charge (same idempotencyKey) — payment_failed only. */
  onRetry: () => void;
  /** Retry fiscal emit standalone — fiscal_failed only. */
  onRetryFiscal: () => void;
  /** Dismiss/collapse form — conflict_409 only. */
  onDismiss: () => void;
  /** True when retrying charge is in-flight. */
  isRetrying: boolean;
  /** True when retrying fiscal emit is in-flight. */
  isFiscalRetrying: boolean;
  className?: string;
}

// ── Component ──────────────────────────────────────────────────────────────

/**
 * Error alert for CobrarSaldoSubform saga.
 * Renders variant-specific UI based on errorState.type.
 */
export function CobrarSaldoSubformErrorAlert({
  errorState,
  onRetry,
  onRetryFiscal,
  onDismiss,
  isRetrying,
  isFiscalRetrying,
  className,
}: CobrarSaldoSubformErrorAlertProps) {
  // ── payment_failed: 503 payment adapter ──
  if (errorState.type === "payment_failed") {
    return (
      <Alert
        variant="destructive"
        className={cn("flex flex-col gap-3", className)}
        data-testid="charge-error-payment"
        role="alert"
      >
        <div className="flex items-start gap-2">
          <XCircle
            className="h-4 w-4 mt-0.5 shrink-0"
            aria-hidden="true"
          />
          <div className="flex flex-col gap-1">
            <AlertTitle>Error al procesar el cobro</AlertTitle>
            <AlertDescription>
              No pudimos procesar el cobro. Intenta de nuevo en unos segundos.
            </AlertDescription>
          </div>
        </div>
        <Button
          type="button"
          variant="destructive"
          size="sm"
          className="self-end"
          onClick={onRetry}
          disabled={isRetrying}
          aria-label="Reintentar cobro"
        >
          {isRetrying ? (
            <>
              <RefreshCw
                className="h-3.5 w-3.5 mr-1.5 animate-spin"
                aria-hidden="true"
              />
              Reintentando...
            </>
          ) : (
            <>
              <RefreshCw className="h-3.5 w-3.5 mr-1.5" aria-hidden="true" />
              Reintentar
            </>
          )}
        </Button>
      </Alert>
    );
  }

  // ── fiscal_failed: charge OK, fiscal emission failed ──
  if (errorState.type === "fiscal_failed") {
    return (
      <Alert
        className={cn(
          "border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20 flex flex-col gap-3",
          className,
        )}
        data-testid="charge-error-fiscal"
        role="alert"
      >
        <div className="flex items-start gap-2">
          <AlertTriangle
            className="h-4 w-4 mt-0.5 shrink-0 text-yellow-600 dark:text-yellow-400"
            aria-hidden="true"
          />
          <div className="flex flex-col gap-1">
            <AlertTitle className="text-yellow-800 dark:text-yellow-300">
              Cobro registrado — comprobante pendiente
            </AlertTitle>
            <AlertDescription className="text-yellow-700 dark:text-yellow-400">
              El cobro fue registrado correctamente. No se pudo emitir el
              comprobante fiscal. Puedes reintentarlo cuando el servicio esté
              disponible.
            </AlertDescription>
          </div>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="self-end border-yellow-500 text-yellow-700 hover:bg-yellow-100 dark:text-yellow-400 dark:hover:bg-yellow-950/40"
          onClick={onRetryFiscal}
          disabled={isFiscalRetrying}
          aria-label="Reintentar emisión de comprobante"
        >
          {isFiscalRetrying ? (
            <>
              <RefreshCw
                className="h-3.5 w-3.5 mr-1.5 animate-spin"
                aria-hidden="true"
              />
              Reintentando...
            </>
          ) : (
            <>
              <RefreshCw className="h-3.5 w-3.5 mr-1.5" aria-hidden="true" />
              Reintentar emisión
            </>
          )}
        </Button>
      </Alert>
    );
  }

  // ── conflict_409: balance already charged by another user ──
  if (errorState.type === "conflict_409") {
    return (
      <Alert
        className={cn("flex flex-col gap-3", className)}
        data-testid="charge-error-conflict"
        role="alert"
      >
        <div className="flex items-start gap-2">
          <Info
            className="h-4 w-4 mt-0.5 shrink-0"
            aria-hidden="true"
          />
          <div className="flex flex-col gap-1">
            <AlertTitle>El saldo ya fue cobrado</AlertTitle>
            <AlertDescription>
              Este saldo ya fue cobrado por otro usuario. La vista se
              actualizará para reflejar el estado actual.
            </AlertDescription>
          </div>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="self-end"
          onClick={onDismiss}
          aria-label="Entendido"
        >
          <CheckCircle2
            className="h-3.5 w-3.5 mr-1.5"
            aria-hidden="true"
          />
          Entendido
        </Button>
      </Alert>
    );
  }

  // ── validation_422: field validation errors ──
  if (errorState.type === "validation_422") {
    return (
      <Alert
        variant="destructive"
        className={className}
        data-testid="charge-error-validation"
        role="alert"
      >
        <XCircle className="h-4 w-4" aria-hidden="true" />
        <AlertTitle>Error de validación</AlertTitle>
        <AlertDescription>{errorState.message}</AlertDescription>
      </Alert>
    );
  }

  // ── server_error / fallback: generic 500 ──
  return (
    <Alert
      variant="destructive"
      className={className}
      data-testid="charge-error-generic"
      role="alert"
    >
      <XCircle className="h-4 w-4" aria-hidden="true" />
      <AlertTitle>Error del servidor</AlertTitle>
      <AlertDescription>
        Ocurrió un error inesperado. Por favor, intenta de nuevo más tarde.
      </AlertDescription>
    </Alert>
  );
}
