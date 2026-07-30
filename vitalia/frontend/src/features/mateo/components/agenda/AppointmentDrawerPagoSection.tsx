// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * AppointmentDrawerPagoSection.tsx — "Pago" accordion section for AppointmentDrawer.
 * T-14 + T-15 vitalia-fase2-valeria-agenda
 *
 * Renders:
 *   - Payment status badge (pagado / con depósito / sin pago)
 *   - Balance due / paid display (via formatTenantMoney)
 *   - <CobrarSaldoSubform /> (T-15) when saldo > 0
 *   - Historical payments list (if any)
 *
 * T-15: CobrarSaldoSubformPlaceholder replaced with real CobrarSaldoSubform.
 *
 * HIPAA-lite: amounts use bucketed cents (no PHI). Currency from appointment data.
 * Master-data: formatTenantMoney() from lib/tenant-locale — NEVER hardcode 'USD'.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.6 + § 6.7 + 06-tickets.yaml T-14 + T-15
 */

import { Receipt, FileText } from "lucide-react";
import { CobrarSaldoSubform } from "./CobrarSaldoSubform";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatMoney } from "@/lib/format/formatMoney";
import { formatTenantDateTime } from "@/lib/format/formatTenantDateTime";
import type { Appointment, AppointmentPayment } from "../../types/agenda.types";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AppointmentDrawerPagoSectionProps {
  /** Full appointment detail from useAppointmentDetail. */
  appointment: Appointment;
  /** Clerk tenant ID — forwarded to CobrarSaldoSubform. */
  tenantId: string;
  /** Tenant currency fallback (from useTenantLocale). */
  tenantCurrency: string;
  /** Tenant locale string for Intl.NumberFormat (e.g., "es-PE"). */
  tenantLocale: string;
  /** Tenant timezone (e.g., "America/Lima") — forwarded for date formatting. */
  tenantTimezone: string;
  /** Whether to auto-emit invoice (tenant.config.auto_emit_invoice). */
  defaultEmitInvoice?: boolean;
}

// ── Status badge config ───────────────────────────────────────────────────────

type PaymentBadgeConfig = {
  label: string;
  className: string;
};

const PAYMENT_STATUS_BADGE: Record<string, PaymentBadgeConfig> = {
  paid: {
    label: "Pagado",
    className: "border-[color:var(--vitalia-success-color)] text-[color:var(--vitalia-success-color)] bg-[color:var(--vitalia-success-color)]/10",
  },
  deposit: {
    label: "Con depósito",
    className: "border-[color:var(--vitalia-warning-color)] text-[color:var(--vitalia-warning-color)] bg-[color:var(--vitalia-warning-color)]/10",
  },
  unpaid: {
    label: "Sin pago",
    className: "border-destructive text-destructive bg-destructive/5",
  },
  no_show: {
    label: "No asistió",
    className: "border-muted-foreground text-muted-foreground bg-muted/20",
  },
};

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Wraps shared formatMoney for nullable cents (returns "—" when null).
 * Converts cents → decimal before calling shared helper (F3 dedup fix).
 */
function formatAmountCents(
  amountCents: number | null,
  currency: string,
  locale: string,
): string {
  if (amountCents === null) return "—";
  return formatMoney(amountCents / 100, currency, locale);
}

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  cash: "Efectivo",
  efectivo: "Efectivo",
  card: "Tarjeta",
  tarjeta: "Tarjeta",
  transfer: "Transferencia",
  transferencia: "Transferencia",
  mercadopago: "MercadoPago",
  mercado_pago: "MercadoPago",
  other: "Otro",
  otro: "Otro",
};

// ── Subcomponents ─────────────────────────────────────────────────────────────

interface PaymentRowProps {
  payment: AppointmentPayment;
  currency: string;
  locale: string;
  timezone: string;
}

function PaymentRow({ payment, currency, locale, timezone }: PaymentRowProps) {
  const effectiveCurrency = payment.currency ?? currency;
  const methodLabel = PAYMENT_METHOD_LABELS[payment.method] ?? payment.method;

  return (
    <div
      className="flex items-center justify-between py-2 border-b border-border/50 last:border-0 text-sm"
      data-testid="payment-row"
    >
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="font-medium">
          {formatAmountCents(payment.amountCents, effectiveCurrency, locale)}
        </span>
        <span className="text-xs text-muted-foreground">
          {methodLabel} · {formatTenantDateTime(payment.createdAt, timezone, locale)}
        </span>
        {payment.createdByLabel && (
          <span className="text-xs text-muted-foreground truncate">
            {payment.createdByLabel}
          </span>
        )}
      </div>
      {payment.fiscalDocUrl ? (
        <a
          href={payment.fiscalDocUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 text-xs text-primary underline-offset-2 hover:underline flex items-center gap-1"
          aria-label="Ver comprobante fiscal"
        >
          <FileText className="h-3.5 w-3.5" aria-hidden="true" />
          {payment.fiscalDocType ?? "Comprobante"}
        </a>
      ) : (
        <span className="shrink-0 text-xs text-muted-foreground flex items-center gap-1">
          <Receipt className="h-3.5 w-3.5" aria-hidden="true" />
          Sin comprobante
        </span>
      )}
    </div>
  );
}

// (CobrarSaldoSubformPlaceholder removed — T-15 ships the real form)

// ── Main Component ─────────────────────────────────────────────────────────────

/**
 * Pago section — balance summary + CobrarSaldoSubform (T-15) + payment history.
 */
export function AppointmentDrawerPagoSection({
  appointment,
  tenantId,
  tenantCurrency,
  tenantLocale,
  tenantTimezone,
  defaultEmitInvoice = true,
}: AppointmentDrawerPagoSectionProps) {
  // Currency: per-appointment override takes precedence over tenant default
  const effectiveCurrency = appointment.currencyOverride ?? appointment.currency ?? tenantCurrency;
  const statusConfig = PAYMENT_STATUS_BADGE[appointment.paymentStatus] ??
    PAYMENT_STATUS_BADGE.unpaid;

  const hasDueBalance =
    appointment.balanceDueCents !== null &&
    appointment.balanceDueCents > 0 &&
    appointment.appointmentStatus !== "CANCELLED" &&
    appointment.appointmentStatus !== "NO_SHOW";

  return (
    <div
      className="flex flex-col gap-4"
      data-testid="pago-section"
    >
      {/* Payment status + balance summary */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Estado de pago:</span>
          <Badge
            variant="outline"
            className={cn("text-xs", statusConfig.className)}
          >
            {statusConfig.label}
          </Badge>
        </div>

        {/* Balance display */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          {appointment.balancePaidCents !== null && (
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">Pagado</span>
              <span className="font-medium text-[color:var(--vitalia-success-color)]">
                {formatAmountCents(appointment.balancePaidCents, effectiveCurrency, tenantLocale)}
              </span>
            </div>
          )}
          {appointment.balanceDueCents !== null && (
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">Saldo pendiente</span>
              <span
                className={cn(
                  "font-medium",
                  appointment.balanceDueCents > 0
                    ? "text-destructive"
                    : "text-[color:var(--vitalia-success-color)]",
                )}
              >
                {formatAmountCents(appointment.balanceDueCents, effectiveCurrency, tenantLocale)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* CobrarSaldoSubform (T-15) — rendered when saldo > 0 */}
      {hasDueBalance && (
        <CobrarSaldoSubform
          appointment={appointment}
          tenantId={tenantId}
          tenantCurrency={tenantCurrency}
          tenantLocale={tenantLocale}
          defaultEmitInvoice={defaultEmitInvoice}
        />
      )}

      {/* Payment history */}
      {appointment.payments.length > 0 && (
        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Historial de pagos
          </span>
          <div
            className="rounded-md border bg-card/50"
            role="list"
            aria-label="Historial de pagos"
          >
            {appointment.payments.map((payment) => (
              <div key={payment.paymentId} role="listitem">
                <PaymentRow
                  payment={payment}
                  currency={effectiveCurrency}
                  locale={tenantLocale}
                  timezone={tenantTimezone}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {appointment.payments.length === 0 && !hasDueBalance && (
        <p className="text-sm text-muted-foreground text-center py-2">
          Sin registros de pago
        </p>
      )}
    </div>
  );
}
