// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-R-planpago
"use client";
/**
 * PlanPagoView.tsx — Leaf 4: Plan de pago (3-cobro wired model).
 *
 * Wires the BE's ThreeChargePricingDTO to 4 editable sections:
 *   1. Precio del tratamiento: price · price_mode · price_publishable
 *   2. Reserva de la cita (seña): enabled · amount · kind
 *   3. Anticipo para iniciar: enabled · amount · kind · ≈equivale (calc, read-only)
 *   4. Financiamiento del saldo: offered · installments · interest_kind ·
 *      finance_partner · ≈por mes (calc, read-only)
 *
 * PATCH rules:
 *   - On ANY field change send the FULL pricing object (price_mode +
 *     price_publishable are required, no BE defaults).
 *   - price lives in TWO places: top-level offer `price` AND `pricing.price`.
 *     When the headline price changes, send { price: v, pricing: { ...full, price: v } }.
 *     For non-price changes send { pricing: { ...full } } (price inside pricing unchanged).
 *   - Autosave 600ms debounce via use-autosave (canon §2.6).
 *   - ONE FloatingAutosaveIndicator per page (canon §2.6).
 *
 * Calculations (client-side, mirrors BE pricing_calc.py):
 *   - advance_equiv: kind==="porcentaje" → price*amount/100 else amount (null if missing)
 *   - reservation_equiv: same formula on reservation
 *   - per_month: (price - reservation_equiv - advance_equiv) / installments
 *     (only when offered && installments>=1 && price!=null)
 *
 * Hydration: uses RHF `values` (NOT defaultValues) so form re-syncs on cache update.
 * When servicio.pricing is null (older services), seeds sensible defaults.
 *
 * T-R-planpago vitalia-fase2-lisa-servicios
 * spec_anchor: 01-spec.md §Workspace Pestaña 4 · mockups/servicio-workspace.html §PLAN DE PAGO
 */

import { useCallback } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Group,
  GroupHeader,
  FloatingAutosaveIndicator,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Switch,
} from "@luana/ui-kit";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { useAutosave } from "@/hooks/use-autosave";
import {
  useServicioDetail,
  usePatchField,
} from "../../../api/servicios";
import type {
  ServicePatchRequest,
  ThreeChargePricing,
  ChargeKind,
  PriceMode,
  ReservationConfig,
  AdvanceConfig,
  FinancingConfig,
} from "../../../types/servicios.types";
import { NumberWithUnit } from "@/components/shared/NumberWithUnit";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import { FieldTooltip } from "../FieldTooltip";

// ── Schema ────────────────────────────────────────────────────────────────────

const reservationSchema = z.object({
  enabled: z.boolean(),
  amount: z.number().nullable(),
  kind: z.enum(["monto", "porcentaje"]),
});

const advanceSchema = z.object({
  enabled: z.boolean(),
  amount: z.number().nullable(),
  kind: z.enum(["monto", "porcentaje"]),
});

const financingSchema = z.object({
  offered: z.boolean(),
  installments: z.number().int().min(1).nullable(),
  interest_kind: z.string().nullable(),
  finance_partner: z.string().nullable(),
});

const planPagoSchema = z
  .object({
    price: z.number().nullable(),
    price_mode: z.enum(["fijo", "rango"]),
    price_publishable: z.boolean(),
    reservation: reservationSchema,
    advance: advanceSchema,
    financing: financingSchema,
  })
  .superRefine((data, ctx) => {
    // BE invariant: financing.offered === true REQUIRES installments >= 1
    if (data.financing.offered && (data.financing.installments === null || data.financing.installments < 1)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["financing", "installments"],
        message: "Ingresa al menos 1 cuota para ofrecer financiamiento",
      });
    }
  });

type PlanPagoFormValues = z.infer<typeof planPagoSchema>;

// ── Default seeding (older services without pricing JSONB) ────────────────────

function buildDefaultPricing(price: number | null, currency: string | null): ThreeChargePricing {
  return {
    price: price ?? null,
    price_mode: "fijo",
    price_publishable: true,
    currency,
    reservation: { enabled: false, amount: null, kind: "monto" },
    advance: { enabled: false, amount: null, kind: "porcentaje" },
    financing: { offered: false, installments: null, interest_kind: null, finance_partner: null },
  };
}

// G2-F14b: the BE serializes Decimal money as JSON strings ("100") to preserve
// precision (FastAPI/Pydantic). The numeric form + NumberWithUnit need real
// numbers — `Number.isFinite("100")` is false → the input renders EMPTY on reload.
// Coerce at the wire→form boundary. (Runtime values are strings despite the
// `number` TS type, so the input is intentionally widened.)
function toNum(v: number | string | null | undefined): number | null {
  if (v === null || v === undefined || v === "") return null;
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n : null;
}

function pricingToFormValues(pricing: ThreeChargePricing, fallbackPrice: number | null): PlanPagoFormValues {
  return {
    price: toNum(pricing.price) ?? toNum(fallbackPrice) ?? null,
    price_mode: pricing.price_mode ?? "fijo",
    price_publishable: pricing.price_publishable ?? true,
    reservation: pricing.reservation
      ? { ...pricing.reservation, amount: toNum(pricing.reservation.amount) }
      : { enabled: false, amount: null, kind: "monto" },
    advance: pricing.advance
      ? { ...pricing.advance, amount: toNum(pricing.advance.amount) }
      : { enabled: false, amount: null, kind: "porcentaje" },
    financing: pricing.financing ?? { offered: false, installments: null, interest_kind: null, finance_partner: null },
  };
}

// G2-F14: full-shape form defaults so the nested objects (reservation/advance/
// financing) ALWAYS exist — even on the first render before the `values` prop
// syncs. Without this, `form.watch("reservation")` is undefined → crash, and
// `form.getValues()` returns a partial pricing → autosave sends incomplete data.
const EMPTY_PLAN_PAGO_DEFAULTS: PlanPagoFormValues = pricingToFormValues(
  buildDefaultPricing(null, null),
  null,
);

// ── Calculations (mirror BE pricing_calc.py) ──────────────────────────────────

function calcChargeEquiv(
  price: number | null,
  amount: number | null,
  kind: ChargeKind,
): number | null {
  if (amount === null || price === null) return null;
  if (kind === "porcentaje") return (price * amount) / 100;
  return amount; // monto fijo
}

function calcPerMonth(
  price: number | null,
  reservationEquiv: number | null,
  advanceEquiv: number | null,
  installments: number | null,
): number | null {
  if (price === null || installments === null || installments < 1) return null;
  const saldo = price - (reservationEquiv ?? 0) - (advanceEquiv ?? 0);
  return saldo / installments;
}

function formatCalc(value: number | null, currency: string): string {
  if (value === null) return "—";
  return `${currency} ${value.toLocaleString("es", { maximumFractionDigits: 0 })}`;
}

// ── Props ─────────────────────────────────────────────────────────────────────

interface PlanPagoViewProps {
  offerId: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function PlanPagoView({ offerId }: PlanPagoViewProps) {
  const { data: servicio } = useServicioDetail({ offerId });
  const locale = useTenantLocale();
  const { mutateAsync: patchAsync } = usePatchField(offerId);

  const saveFn = useCallback(
    (patch: ServicePatchRequest) => patchAsync(patch),
    [patchAsync],
  );
  const { schedule, status } = useAutosave<ServicePatchRequest>({ saveFn });

  // Derive effective pricing (seed defaults for older services)
  const effectivePricing: ThreeChargePricing =
    servicio?.pricing ??
    buildDefaultPricing(servicio?.price ?? null, servicio?.currency ?? null);

  const form = useForm<PlanPagoFormValues>({
    resolver: zodResolver(planPagoSchema),
    // G2-F14: defaultValues seeds the FULL shape (nested objects never undefined);
    // `values` re-hydrates the form when the servicio detail loads/updates post-save
    // (G2-F6 pattern). Both together = no first-render crash + cache re-sync.
    defaultValues: EMPTY_PLAN_PAGO_DEFAULTS,
    values: servicio ? pricingToFormValues(effectivePricing, servicio.price ?? null) : undefined,
  });

  const currency = servicio?.currency ?? locale.currency;

  // ── Loading skeleton ────────────────────────────────────────────────────────

  if (!servicio) {
    return (
      <div className="p-6 space-y-4" aria-busy="true">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 bg-muted rounded-md animate-pulse" />
        ))}
      </div>
    );
  }

  // ── Helpers to build full pricing patch ──────────────────────────────────────

  /**
   * Build the complete ThreeChargePricing from current form state.
   * price_mode + price_publishable are required by the BE — always included.
   */
  function buildFullPricingFromForm(overrides: Partial<PlanPagoFormValues> = {}): ThreeChargePricing {
    const current = form.getValues();
    const merged = { ...current, ...overrides };
    return {
      price: merged.price,
      price_mode: merged.price_mode,
      price_publishable: merged.price_publishable,
      // RN-23: currency never edited here — send servicio.currency as-is
      // Safe: called only after the `if (!servicio)` guard above the form render
      currency: (servicio as NonNullable<typeof servicio>).currency ?? null,
      reservation: merged.reservation as ReservationConfig,
      advance: merged.advance as AdvanceConfig,
      financing: merged.financing as FinancingConfig,
    };
  }

  // ── Live calculated values ────────────────────────────────────────────────

  const watchedPrice = form.watch("price");
  const watchedAdvance = form.watch("advance");
  const watchedReservation = form.watch("reservation");
  const watchedFinancing = form.watch("financing");

  // Defensive `?.`: belt-and-suspenders against any `values`-sync timing where a
  // nested watch is briefly undefined (the defaultValues above is the real guard).
  const reservationEquiv = watchedReservation?.enabled
    ? calcChargeEquiv(watchedPrice, watchedReservation.amount, watchedReservation.kind)
    : null;

  const advanceEquiv = watchedAdvance?.enabled
    ? calcChargeEquiv(watchedPrice, watchedAdvance.amount, watchedAdvance.kind)
    : null;

  const perMonth = watchedFinancing?.offered
    ? calcPerMonth(watchedPrice, reservationEquiv, advanceEquiv, watchedFinancing.installments)
    : null;

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="p-5 md:p-6 space-y-6 pb-24">

      {/* ── 1. Precio del tratamiento ─────────────────────────────────────── */}
      <Group accentVar="--agent-lisa">
        <GroupHeader title="Precio del tratamiento" whatFor="precio base del tratamiento" />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Price */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5">
              <Label htmlFor="price">Precio</Label>
              <FieldTooltip
                content="La moneda sale de la configuración de tu clínica (no se edita aquí). Para cambiarla: Configuración → Cuenta / Localización."
              />
              <span className="text-xs text-muted-foreground ml-auto">{currency}</span>
            </div>
            <Controller
              control={form.control}
              name="price"
              render={({ field, fieldState }) => (
                <>
                  <NumberWithUnit
                    value={field.value ?? 0}
                    onChange={(v) => {
                      field.onChange(v);
                      // price lives in TWO places: top-level AND inside pricing
                      const fullPricing = buildFullPricingFromForm({ price: v });
                      schedule({ price: v, pricing: fullPricing });
                    }}
                    unit={currency}
                    min={0}
                    step={50}
                    aria-invalid={!!fieldState.error}
                    aria-label="Precio del tratamiento"
                  />
                  {fieldState.error && (
                    <p className="text-sm text-destructive" role="alert">
                      {fieldState.error.message}
                    </p>
                  )}
                </>
              )}
            />
          </div>

          {/* price_mode */}
          <div className="space-y-2">
            <Label htmlFor="price_mode">Modo</Label>
            <Controller
              control={form.control}
              name="price_mode"
              render={({ field }) => (
                <Select
                  value={field.value}
                  onValueChange={(v) => {
                    field.onChange(v as PriceMode);
                    schedule({ pricing: buildFullPricingFromForm({ price_mode: v as PriceMode }) });
                  }}
                >
                  <SelectTrigger id="price_mode" aria-label="Modo de precio">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fijo">Fijo</SelectItem>
                    <SelectItem value="rango">Rango (&ldquo;desde&rdquo;)</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>
        </div>

        {/* price_publishable */}
        <div className="flex items-center gap-3 mt-2">
          <Controller
            control={form.control}
            name="price_publishable"
            render={({ field }) => (
              <Switch
                id="price_publishable"
                checked={field.value}
                onCheckedChange={(checked) => {
                  field.onChange(checked);
                  schedule({ pricing: buildFullPricingFromForm({ price_publishable: checked }) });
                }}
                aria-label="Precio publicable"
              />
            )}
          />
          <Label htmlFor="price_publishable" className="cursor-pointer">
            Adrián puede decir el precio en el chat{" "}
            <span className="text-muted-foreground text-xs font-normal">
              (si lo apagas, agenda una valoración en vez de dar el precio)
            </span>
          </Label>
        </div>
      </Group>

      {/* ── 2. Reserva de la cita ────────────────────────────────────────── */}
      <Group>
        <GroupHeader
          title="Reserva de la cita"
          whatFor='la "seña" para apartar el turno'
        />
        <p className="text-sm text-muted-foreground -mt-1">
          Monto pequeño que el paciente paga para{" "}
          <strong>apartar su cita</strong> (reduce inasistencias &middot; reserva prepagada de
          Vitalia). <strong>Se descuenta del total.</strong>
        </p>

        {/* enabled */}
        <div className="flex items-center gap-3">
          <Controller
            control={form.control}
            name="reservation.enabled"
            render={({ field }) => (
              <Switch
                id="reservation_enabled"
                checked={field.value}
                onCheckedChange={(checked) => {
                  field.onChange(checked);
                  schedule({
                    pricing: buildFullPricingFromForm({
                      reservation: { ...form.getValues("reservation"), enabled: checked },
                    }),
                  });
                }}
                aria-label="Pide reserva para agendar"
              />
            )}
          />
          <Label htmlFor="reservation_enabled" className="cursor-pointer">
            Pide reserva para agendar
          </Label>
        </div>

        {/* amount + kind (always visible for discovery UX) */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label htmlFor="reservation_amount">Monto de la reserva</Label>
            <Controller
              control={form.control}
              name="reservation.amount"
              render={({ field }) => (
                <NumberWithUnit
                  value={field.value ?? 0}
                  onChange={(v) => {
                    field.onChange(v);
                    schedule({
                      pricing: buildFullPricingFromForm({
                        reservation: { ...form.getValues("reservation"), amount: v },
                      }),
                    });
                  }}
                  unit={form.watch("reservation.kind") === "porcentaje" ? "%" : currency}
                  min={0}
                  step={form.watch("reservation.kind") === "porcentaje" ? 1 : 50}
                  aria-label="Monto de la reserva"
                />
              )}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="reservation_kind">Tipo</Label>
            <Controller
              control={form.control}
              name="reservation.kind"
              render={({ field }) => (
                <Select
                  value={field.value}
                  onValueChange={(v) => {
                    field.onChange(v as ChargeKind);
                    schedule({
                      pricing: buildFullPricingFromForm({
                        reservation: { ...form.getValues("reservation"), kind: v as ChargeKind },
                      }),
                    });
                  }}
                >
                  <SelectTrigger id="reservation_kind" aria-label="Tipo de reserva">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="monto">Monto fijo</SelectItem>
                    <SelectItem value="porcentaje">% del total</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>
        </div>
      </Group>

      {/* ── 3. Anticipo para iniciar ──────────────────────────────────────── */}
      <Group>
        <GroupHeader
          title="Anticipo para iniciar"
          whatFor="pago inicial del tratamiento"
        />
        <p className="text-sm text-muted-foreground -mt-1">
          Pago adelantado sobre el <strong>costo del tratamiento</strong> que el paciente da
          para <strong>empezar</strong> (aparte de la reserva). Clave en implantes, ortodoncia
          y cirugía.
        </p>

        {/* enabled */}
        <div className="flex items-center gap-3">
          <Controller
            control={form.control}
            name="advance.enabled"
            render={({ field }) => (
              <Switch
                id="advance_enabled"
                checked={field.value}
                onCheckedChange={(checked) => {
                  field.onChange(checked);
                  schedule({
                    pricing: buildFullPricingFromForm({
                      advance: { ...form.getValues("advance"), enabled: checked },
                    }),
                  });
                }}
                aria-label="Requiere anticipo para iniciar"
              />
            )}
          />
          <Label htmlFor="advance_enabled" className="cursor-pointer">
            Requiere anticipo para iniciar
          </Label>
        </div>

        {/* amount + kind + ≈equivale */}
        <div className="grid grid-cols-3 gap-3">
          <div className="space-y-2">
            <div className="flex items-center gap-1">
              <Label htmlFor="advance_amount">Anticipo</Label>
              <FieldTooltip content="Pago inicial sobre el costo del tratamiento para empezar (aparte de la reserva de la cita). Ej: 30% del total antes de la primera sesión de implante." />
            </div>
            <Controller
              control={form.control}
              name="advance.amount"
              render={({ field }) => (
                <NumberWithUnit
                  value={field.value ?? 0}
                  onChange={(v) => {
                    field.onChange(v);
                    schedule({
                      pricing: buildFullPricingFromForm({
                        advance: { ...form.getValues("advance"), amount: v },
                      }),
                    });
                  }}
                  unit={form.watch("advance.kind") === "porcentaje" ? "%" : currency}
                  min={0}
                  step={form.watch("advance.kind") === "porcentaje" ? 1 : 50}
                  aria-label="Monto del anticipo"
                />
              )}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="advance_kind">Tipo</Label>
            <Controller
              control={form.control}
              name="advance.kind"
              render={({ field }) => (
                <Select
                  value={field.value}
                  onValueChange={(v) => {
                    field.onChange(v as ChargeKind);
                    schedule({
                      pricing: buildFullPricingFromForm({
                        advance: { ...form.getValues("advance"), kind: v as ChargeKind },
                      }),
                    });
                  }}
                >
                  <SelectTrigger id="advance_kind" aria-label="Tipo de anticipo">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="porcentaje">% del total</SelectItem>
                    <SelectItem value="monto">Monto fijo</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-1">
              <Label htmlFor="advance_equiv" className="text-muted-foreground text-xs">
                ≈ equivale a
              </Label>
              <FieldTooltip content="Se calcula solo a partir del % y el precio del tratamiento. No se edita." />
            </div>
            <Input
              id="advance_equiv"
              value={formatCalc(advanceEquiv, currency)}
              readOnly
              disabled
              aria-label="Equivale a (calculado)"
              className="bg-muted"
            />
          </div>
        </div>
      </Group>

      {/* ── 4. Financiamiento del saldo ───────────────────────────────────── */}
      <Group>
        <GroupHeader
          title="Financiamiento del saldo"
          whatFor="cuotas del resto"
        />

        {/* offered */}
        <div className="flex items-center gap-3">
          <Controller
            control={form.control}
            name="financing.offered"
            render={({ field }) => (
              <Switch
                id="financing_offered"
                checked={field.value}
                onCheckedChange={(checked) => {
                  field.onChange(checked);
                  schedule({
                    pricing: buildFullPricingFromForm({
                      financing: { ...form.getValues("financing"), offered: checked },
                    }),
                  });
                }}
                aria-label="Ofrece pago en cuotas"
              />
            )}
          />
          <Label htmlFor="financing_offered" className="cursor-pointer">
            Ofrece pago en cuotas
          </Label>
        </div>

        {/* installments + interest_kind + ≈por mes */}
        <div className="grid grid-cols-3 gap-3">
          <div className="space-y-2">
            <Label htmlFor="financing_installments">Cuotas</Label>
            <Controller
              control={form.control}
              name="financing.installments"
              render={({ field, fieldState }) => (
                <>
                  <Input
                    id="financing_installments"
                    type="number"
                    min={1}
                    value={field.value ?? ""}
                    onChange={(e) => {
                      const v = e.target.value === "" ? null : Number(e.target.value);
                      field.onChange(v);
                      schedule({
                        pricing: buildFullPricingFromForm({
                          financing: { ...form.getValues("financing"), installments: v },
                        }),
                      });
                    }}
                    aria-label="Número de cuotas"
                    aria-invalid={!!fieldState.error}
                  />
                  {fieldState.error && (
                    <p className="text-xs text-destructive" role="alert">
                      {fieldState.error.message}
                    </p>
                  )}
                </>
              )}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="financing_interest">Interés</Label>
            <Controller
              control={form.control}
              name="financing.interest_kind"
              render={({ field }) => (
                <Select
                  value={field.value ?? ""}
                  onValueChange={(v) => {
                    field.onChange(v || null);
                    schedule({
                      pricing: buildFullPricingFromForm({
                        financing: { ...form.getValues("financing"), interest_kind: v || null },
                      }),
                    });
                  }}
                >
                  <SelectTrigger id="financing_interest" aria-label="Tipo de interés">
                    <SelectValue placeholder="Sin interés (MSI)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sin_interes">Sin interés (MSI)</SelectItem>
                    <SelectItem value="con_interes">Con interés</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-1">
              <Label htmlFor="per_month" className="text-muted-foreground text-xs">
                ≈ por mes
              </Label>
              <FieldTooltip content="Se calcula solo: (precio − reserva − anticipo) ÷ cuotas. No se edita." />
            </div>
            <Input
              id="per_month"
              value={formatCalc(perMonth, currency)}
              readOnly
              disabled
              aria-label="Pago mensual calculado"
              className="bg-muted"
            />
          </div>
        </div>

        {/* finance_partner — maps to "socio financiero"; medios de pago has no BE field, omitted */}
        <div className="space-y-2">
          <Label htmlFor="finance_partner">Socio financiero</Label>
          <Controller
            control={form.control}
            name="financing.finance_partner"
            render={({ field }) => (
              <Input
                id="finance_partner"
                value={field.value ?? ""}
                onChange={(e) => {
                  const v = e.target.value || null;
                  field.onChange(v);
                  schedule({
                    pricing: buildFullPricingFromForm({
                      financing: { ...form.getValues("financing"), finance_partner: v },
                    }),
                  });
                }}
                placeholder="Ej: Mercado Pago, Kueski, —"
                aria-label="Socio financiero"
              />
            )}
          />
        </div>
      </Group>

      {/* Autosave indicator — ONE per page (canon §2.6) */}
      <FloatingAutosaveIndicator status={status} />
    </div>
  );
}
