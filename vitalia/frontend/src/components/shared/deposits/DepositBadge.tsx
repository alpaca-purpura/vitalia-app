// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
/**
 * DepositBadge — visual badge for prepaid booking deposit status.
 *
 * Scaffold stub. Full implementation (with real payment/booking integration)
 * arrives in scheduling-prepaid story (Slice 2+).
 *
 * Per vitalia design: booking reservas prepagadas — badge shows deposit state.
 * All colors via vt-* CSS classes from globals.css (no hsl literals in TSX).
 */

import { cn } from "@/lib/cn";

export type DepositStatus =
  | "pending" /* Pendiente de pago */
  | "paid" /* Pagado y confirmado */
  | "partial" /* Pago parcial */
  | "refunded" /* Reembolsado */
  | "expired"; /* Vencido sin pago */

export interface DepositBadgeProps {
  /** Deposit payment status */
  status: DepositStatus;
  /** Deposit amount (non-PHI) */
  amount?: number;
  /** Currency code (from useTenantLocale — NEVER hardcoded 'USD') */
  currency?: string;
  /** Small size variant */
  size?: "sm" | "md";
  /** Additional CSS classes */
  className?: string;
}

const STATUS_LABELS: Record<DepositStatus, string> = {
  pending: "Pendiente",
  paid: "Pagado",
  partial: "Parcial",
  refunded: "Reembolsado",
  expired: "Vencido",
};

const STATUS_CLASSES: Record<DepositStatus, string> = {
  pending: "vt-bg-warning-12 vt-text-warning vt-border-warning-30 border",
  paid: "vt-bg-success-12 vt-text-success vt-border-success-30 border",
  partial: "vt-bg-cian-8 vt-text-cian vt-border-cian border",
  refunded: "vt-bg-muted vt-text-muted vt-border border",
  expired: "vt-bg-danger-12 vt-text-danger vt-border-danger-30 border",
};

/**
 * Compact deposit status badge for booking cards.
 */
export function DepositBadge({
  status,
  amount,
  currency,
  size = "md",
  className,
}: DepositBadgeProps) {
  const label = STATUS_LABELS[status];
  const statusClass = STATUS_CLASSES[status];

  const amountDisplay =
    amount !== undefined && currency
      ? ` · ${currency} ${amount.toLocaleString("es-419", {
          minimumFractionDigits: 0,
          maximumFractionDigits: 2,
        })}`
      : "";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-medium rounded-[var(--radius-pill)]",
        size === "sm" ? "text-[10px] px-2 py-0.5" : "text-xs px-2.5 py-1",
        statusClass,
        className,
      )}
      aria-label={`Depósito: ${label}${amountDisplay}`}
      role="status"
    >
      {label}
      {amountDisplay && <span className="tabular-nums">{amountDisplay}</span>}
    </span>
  );
}
