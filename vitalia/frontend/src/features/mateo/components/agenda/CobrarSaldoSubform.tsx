// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * CobrarSaldoSubform.tsx — Inline cobro (payment) subform for AppointmentDrawer.
 * T-15 vitalia-fase2-valeria-agenda — ★ corazón valor F2-S1
 *
 * RHF + Zod ChargeRequestSchema (discriminated union by currency).
 * Renders inside AppointmentDrawerPagoSection when saldo > 0.
 *
 * Form fields:
 *   - amountCents: numeric (displayed as decimal, stored as cents)
 *   - method: PaymentMethod select
 *   - emitInvoice: boolean checkbox
 *   - fiscalDocType: select — shown only when emitInvoice=true, options vary by currency
 *   - notes: optional textarea (max 500)
 *   - [Más opciones] collapsible:
 *     - currencyOverride: currency select (hidden by default)
 *   - idempotencyKey: UUID v4, generated on mount via useRef (never shown to user)
 *
 * Saga error handling (3 states):
 *   - payment_failed (503): Alert destructive + Reintentar (same idempotencyKey)
 *   - fiscal_failed (503 post-charge): Alert warning + Reintentar emisión standalone
 *   - conflict_409: Alert "saldo ya cobrado" + Entendido (auto-invalidate + collapse)
 *   - validation_422: inline field errors
 *   - server_error (500): Alert generic
 *
 * HIPAA-lite: amount + method are NOT PHI — no masking needed here.
 * PHI nunca en URL/searchParams (POST body only).
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.7 + 01-spec.md A1-A9 + 06-tickets.yaml T-15
 */

import { useCallback, useRef, useState, useEffect } from "react";
import { useForm, useWatch, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQueryClient } from "@tanstack/react-query";
import { CreditCard, Loader2 } from "lucide-react";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { cn } from "@/lib/utils";
import { ApiError } from "@/lib/fetch-client";
import { ChargeRequestSchema } from "../../types/agenda-schema";
import { useChargeAppointment, useEmitFiscalDoc, agendaKeys } from "../../api/agenda";
import { showChargeSuccessToast } from "./CobrarSaldoSubformSuccessToast";
import { CobrarSaldoSubformErrorAlert } from "./CobrarSaldoSubformErrorAlert";
import type { Appointment } from "../../types/agenda.types";
import type { ChargeResponseDTO } from "../../types/agenda-schema";

// ── Types ──────────────────────────────────────────────────────────────────

/** Discriminated union of error states for saga handling. */
export type ChargeErrorState =
  | { type: "payment_failed"; message: string }
  | {
      type: "fiscal_failed";
      message: string;
      paymentId: string;
      fiscalDocType: string | null;
    }
  | { type: "conflict_409"; message: string }
  | { type: "validation_422"; message: string }
  | { type: "server_error"; message: string };

/**
 * Flat working form type for RHF (avoids discriminated union complexity).
 * Validated via ChargeRequestSchema on submit.
 */
const ChargeFormWorkingSchema = z.object({
  appointmentId: z.string().uuid(),
  amountCents: z
    .number()
    .int()
    .positive("El monto debe ser mayor a cero"),
  method: z.enum(["cash", "card", "transfer", "mercadopago", "other"]),
  currency: z.string().min(3).max(3),
  emitInvoice: z.boolean(),
  fiscalDocType: z.string().optional(),
  notes: z.string().max(500).optional(),
  idempotencyKey: z.string().uuid(),
});

type ChargeFormWorking = z.infer<typeof ChargeFormWorkingSchema>;

// ── Props ──────────────────────────────────────────────────────────────────

export interface CobrarSaldoSubformProps {
  /** Full appointment detail — provides balanceDueCents, currency, etc. */
  appointment: Appointment;
  /** Clerk tenant ID — for useChargeAppointment + query invalidation. */
  tenantId: string;
  /** Tenant currency fallback (from useTenantLocale). */
  tenantCurrency: string;
  /** Tenant locale string for Intl.NumberFormat (e.g., "es-PE"). */
  tenantLocale: string;
  /** Whether emit invoice defaults to true (tenant.config.auto_emit_invoice). */
  defaultEmitInvoice?: boolean;
  /** Callback when charge succeeds — parent can collapse or refresh. */
  onSuccess?: (response: ChargeResponseDTO) => void;
  className?: string;
}

// ── Constants ──────────────────────────────────────────────────────────────

const PAYMENT_METHOD_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "cash", label: "Efectivo" },
  { value: "card", label: "Tarjeta" },
  { value: "transfer", label: "Transferencia" },
  { value: "mercadopago", label: "MercadoPago" },
  { value: "other", label: "Otro" },
];

const CURRENCY_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "ARS", label: "ARS — Peso argentino" },
  { value: "PEN", label: "PEN — Sol peruano" },
  { value: "MXN", label: "MXN — Peso mexicano" },
  { value: "COP", label: "COP — Peso colombiano" },
  { value: "CLP", label: "CLP — Peso chileno" },
  { value: "USD", label: "USD — Dólar americano" },
];

/**
 * Fiscal doc type options per currency (mirrors ChargeRequestSchema discriminator).
 */
const FISCAL_DOC_OPTIONS_BY_CURRENCY: Record<
  string,
  Array<{ value: string; label: string }>
> = {
  PEN: [
    { value: "boleta", label: "Boleta" },
    { value: "factura", label: "Factura" },
  ],
  ARS: [
    { value: "factura_b", label: "Factura B" },
    { value: "factura_a", label: "Factura A" },
    { value: "recibo", label: "Recibo" },
  ],
  MXN: [
    { value: "cfdi", label: "CFDI" },
    { value: "ticket", label: "Ticket" },
  ],
  USD: [
    { value: "ticket", label: "Ticket" },
    { value: "factura", label: "Factura" },
  ],
  COP: [{ value: "ticket", label: "Ticket" }],
  CLP: [
    { value: "boleta", label: "Boleta" },
    { value: "factura", label: "Factura" },
  ],
};

// ── Helpers ────────────────────────────────────────────────────────────────

function getFiscalDocOptions(
  currency: string,
): Array<{ value: string; label: string }> {
  return FISCAL_DOC_OPTIONS_BY_CURRENCY[currency] ?? [];
}

function centsToDecimal(cents: number | null): number {
  if (cents === null) return 0;
  return Math.round(cents) / 100;
}

function decimalToCents(decimal: number): number {
  return Math.round(decimal * 100);
}

// ── Main Component ─────────────────────────────────────────────────────────

/**
 * CobrarSaldoSubform — inline payment subform.
 * Replaces CobrarSaldoSubformPlaceholder from T-14 when saldo > 0.
 */
export function CobrarSaldoSubform({
  appointment,
  tenantId,
  tenantCurrency,
  tenantLocale,
  defaultEmitInvoice = true,
  onSuccess,
  className,
}: CobrarSaldoSubformProps) {
  // ── Idempotency key (stable across retries) ──
  const idempotencyKeyRef = useRef<string>(crypto.randomUUID());

  // ── Effective currency ──
  const effectiveCurrency =
    appointment.currencyOverride ?? appointment.currency ?? tenantCurrency;

  // ── RHF setup using flat working schema ──
  const form = useForm<ChargeFormWorking>({
    resolver: zodResolver(ChargeFormWorkingSchema),
    defaultValues: {
      appointmentId: appointment.appointmentId,
      amountCents: appointment.balanceDueCents ?? 0,
      method: "cash",
      currency: effectiveCurrency,
      emitInvoice: defaultEmitInvoice,
      fiscalDocType: undefined,
      notes: "",
      idempotencyKey: idempotencyKeyRef.current,
    },
  });

  // ── Error saga state ──
  const [errorState, setErrorState] = useState<ChargeErrorState | null>(null);
  const [lastChargeResponse, setLastChargeResponse] =
    useState<ChargeResponseDTO | null>(null);

  // ── Display amount (decimal from cents) ──
  const watchedAmountCents = form.watch("amountCents");
  const displayAmount = centsToDecimal(watchedAmountCents ?? null);

  // ── Mutations ──
  const queryClient = useQueryClient();
  const chargeMutation = useChargeAppointment(tenantId);
  const fiscalMutation = useEmitFiscalDoc(tenantId);

  // ── Watched values for conditional rendering ──
  const emitInvoice = useWatch({ control: form.control, name: "emitInvoice" });
  const currentCurrency = useWatch({ control: form.control, name: "currency" });
  const fiscalDocOptions = getFiscalDocOptions(currentCurrency ?? effectiveCurrency);

  // Reset fiscalDocType when currency changes.
  // form.setValue is stable per RHF docs. Only re-run when currency changes.
  useEffect(() => {
    form.setValue("fiscalDocType", undefined);
  }, [currentCurrency, form]);

  // ── Saga: handle charge success ──
  const handleChargeSuccess = useCallback(
    (response: ChargeResponseDTO) => {
      setLastChargeResponse(response);
      setErrorState(null);

      showChargeSuccessToast({ response, tenantLocale });

      void queryClient.invalidateQueries({
        queryKey: agendaKeys.all(tenantId),
      });

      if (response.fiscalEmissionStatus === "failed") {
        setErrorState({
          type: "fiscal_failed",
          message: "Cobro registrado. Comprobante pendiente.",
          paymentId: response.paymentId,
          fiscalDocType: response.fiscalDocId,
        });
        return;
      }

      onSuccess?.(response);
    },
    [queryClient, tenantId, tenantLocale, onSuccess],
  );

  // ── Saga: handle charge error ──
  const handleChargeError = useCallback(
    (error: Error) => {
      if (error instanceof ApiError) {
        if (error.status === 409) {
          setErrorState({
            type: "conflict_409",
            message: "El saldo ya fue cobrado por otro usuario.",
          });
          void queryClient.invalidateQueries({
            queryKey: agendaKeys.all(tenantId),
          });
          return;
        }
        if (error.status === 422) {
          setErrorState({
            type: "validation_422",
            message: error.message || "Error de validación en los datos del cobro.",
          });
          return;
        }
        if (error.status === 503 || error.status === 502) {
          setErrorState({
            type: "payment_failed",
            message: "El servicio de pagos no está disponible. Intenta de nuevo.",
          });
          return;
        }
      }
      setErrorState({
        type: "server_error",
        message: "Error inesperado. Por favor, intenta más tarde.",
      });
    },
    [queryClient, tenantId],
  );

  // ── Submit handler ──
  const onSubmit = useCallback(
    (values: ChargeFormWorking) => {
      setErrorState(null);

      // Validate with full ChargeRequestSchema (discriminated union)
      const parseResult = ChargeRequestSchema.safeParse(values);
      if (!parseResult.success) {
        const firstError = parseResult.error.issues[0];
        setErrorState({
          type: "validation_422",
          message: firstError?.message ?? "Error de validación.",
        });
        return;
      }

      chargeMutation.mutate(
        {
          appointmentId: appointment.appointmentId,
          payload: values as Record<string, unknown>,
          idempotencyKey: idempotencyKeyRef.current,
        },
        {
          onSuccess: handleChargeSuccess,
          onError: handleChargeError,
        },
      );
    },
    [appointment.appointmentId, chargeMutation, handleChargeSuccess, handleChargeError],
  );

  // ── Retry payment (same idempotencyKey) ──
  const handleRetryPayment = useCallback(() => {
    void form.handleSubmit(onSubmit)();
  }, [form, onSubmit]);

  // ── Retry fiscal emission standalone ──
  const handleRetryFiscal = useCallback(() => {
    if (!lastChargeResponse) return;
    const docType = form.getValues("fiscalDocType") ?? "ticket";
    fiscalMutation.mutate(
      {
        paymentId: lastChargeResponse.paymentId,
        docType: docType as "factura" | "boleta" | "ticket",
      },
      {
        onSuccess: () => {
          setErrorState(null);
          void queryClient.invalidateQueries({
            queryKey: agendaKeys.all(tenantId),
          });
        },
      },
    );
  }, [lastChargeResponse, fiscalMutation, form, queryClient, tenantId]);

  // ── Dismiss 409 conflict ──
  const handleDismissConflict = useCallback(() => {
    setErrorState(null);
    form.reset();
  }, [form]);

  const isPending = chargeMutation.isPending;

  return (
    <div
      className={cn("flex flex-col gap-3", className)}
      data-testid="cobrar-saldo-subform"
    >
      {/* Error alert */}
      {errorState && (
        <CobrarSaldoSubformErrorAlert
          errorState={errorState}
          onRetry={handleRetryPayment}
          onRetryFiscal={handleRetryFiscal}
          onDismiss={handleDismissConflict}
          isRetrying={isPending}
          isFiscalRetrying={fiscalMutation.isPending}
        />
      )}

      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-4"
          aria-label="Formulario de cobro"
          noValidate
        >
          {/* ── Row 1: Amount + Method ── */}
          <div className="grid grid-cols-2 gap-3">
            {/* Amount */}
            <FormField
              control={form.control}
              name="amountCents"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Monto</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      inputMode="decimal"
                      step="0.01"
                      min="0.01"
                      placeholder="0.00"
                      aria-label="Monto a cobrar"
                      value={displayAmount}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value);
                        field.onChange(isNaN(val) ? 0 : decimalToCents(val));
                      }}
                      onBlur={field.onBlur}
                      ref={field.ref}
                      disabled={isPending}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Method */}
            <FormField
              control={form.control}
              name="method"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Método de pago</FormLabel>
                  <FormControl>
                    <select
                      className={cn(
                        "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm",
                        "transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                        "disabled:cursor-not-allowed disabled:opacity-50",
                      )}
                      value={field.value}
                      onChange={field.onChange}
                      onBlur={field.onBlur}
                      ref={field.ref}
                      aria-label="Método de pago"
                      disabled={isPending}
                    >
                      {PAYMENT_METHOD_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          {/* ── Row 2: Emit invoice checkbox ── */}
          <Controller
            control={form.control}
            name="emitInvoice"
            render={({ field }) => (
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="emitInvoice"
                  className="h-4 w-4 rounded border-input accent-primary cursor-pointer"
                  checked={field.value}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  ref={field.ref}
                  aria-label="Emitir comprobante"
                  disabled={isPending}
                />
                <label
                  htmlFor="emitInvoice"
                  className="text-sm cursor-pointer font-normal leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Emitir comprobante
                </label>
              </div>
            )}
          />

          {/* ── Row 3: Fiscal doc type (conditional on emitInvoice) ── */}
          {emitInvoice && (
            <FormField
              control={form.control}
              name="fiscalDocType"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tipo de comprobante</FormLabel>
                  <FormControl>
                    <select
                      className={cn(
                        "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm",
                        "transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                        "disabled:cursor-not-allowed disabled:opacity-50",
                      )}
                      value={field.value ?? ""}
                      onChange={(e) =>
                        field.onChange(e.target.value || undefined)
                      }
                      onBlur={field.onBlur}
                      ref={field.ref}
                      aria-label="Tipo de comprobante"
                      disabled={isPending}
                    >
                      <option value="">Selecciona tipo...</option>
                      {fiscalDocOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          )}

          {/* ── Row 4: Notes (optional) ── */}
          <FormField
            control={form.control}
            name="notes"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Notas</FormLabel>
                <FormControl>
                  <Textarea
                    placeholder="Observaciones del cobro (opcional)"
                    rows={2}
                    className="resize-none text-sm"
                    maxLength={500}
                    aria-label="Notas"
                    disabled={isPending}
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* ── Más opciones: currency override ── */}
          <Accordion type="single" collapsible>
            <AccordionItem value="mas-opciones" className="border-0">
              <AccordionTrigger
                className="py-1 text-xs text-muted-foreground hover:text-foreground hover:no-underline"
                aria-label="Más opciones"
              >
                Más opciones
              </AccordionTrigger>
              <AccordionContent className="pt-2">
                <FormField
                  control={form.control}
                  name="currency"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Moneda</FormLabel>
                      <FormControl>
                        <select
                          className={cn(
                            "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm",
                            "transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                            "disabled:cursor-not-allowed disabled:opacity-50",
                          )}
                          value={field.value}
                          onChange={field.onChange}
                          onBlur={field.onBlur}
                          ref={field.ref}
                          aria-label="Moneda"
                          disabled={isPending}
                        >
                          {CURRENCY_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          {/* ── Submit button ── */}
          <Button
            type="submit"
            className="w-full"
            disabled={isPending}
            aria-busy={isPending}
          >
            {isPending ? (
              <>
                <Loader2
                  className="h-4 w-4 mr-2 animate-spin"
                  aria-hidden="true"
                />
                Procesando...
              </>
            ) : (
              <>
                <CreditCard className="h-4 w-4 mr-2" aria-hidden="true" />
                Cobrar
              </>
            )}
          </Button>
        </form>
      </Form>
    </div>
  );
}
