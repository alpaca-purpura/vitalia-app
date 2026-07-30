// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-R3
"use client";
/**
 * ResumenView.tsx — Leaf 1: Resumen del servicio.
 *
 * 6 collapsible groups (CollapsibleSection from @luana/ui-kit, T-R0):
 *   1. Identidad (defaultOpen): nombre · categoría · peldaño
 *   2. Qué es: descripción larga · incluye · excluye · garantía · variantes
 *   3. El procedimiento: pasos · anestesia/dolor · preparación · cuidados · downtime
 *   4. Resultados: resultado esperado · timing · lifespan · expectativas realistas
 *   5. Riesgos: riesgos/efectos · señales de alarma
 *   6. Modalidad y agenda: modalidad · conditionals (session/recurrence interval) ·
 *      duración cita inicial · tipo de cita
 *
 * All rich fields hydrated from servicio (post T-R1 BE widening).
 * Autosave on-change 600ms (canon §2.6 — ONE FloatingAutosaveIndicator per page).
 * Modality conditionals: sesiones→session_interval / recurrente→recurrence_interval.
 *
 * T-R3 changes over T-7:
 *   - 6 flat <Group> → 6 <CollapsibleSection> (Identidad defaultOpen)
 *   - ALL rich field .value bound from servicio.*
 *   - ALL onChange → schedule({ field: value }) autosave
 *   - VariantsRepeater hydrated: value={servicio.variants ?? []} + currency canon
 *   - Modality conditionals wired via form.watch("modality")
 *   - initial_appt_duration_minutes bound from servicio (was hardcoded 0)
 *   - initial_appt_type bound + autosave (F3 — RN-32)
 *
 * spec_anchor: 01-spec.md §Workspace Pestaña 1 · 03-arch-reconcile-delta.md §C.2
 */

import { useCallback, useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  CollapsibleSection,
  FloatingAutosaveIndicator,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@luana/ui-kit";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useAutosave } from "@/hooks/use-autosave";
import {
  useServicioDetail,
  usePatchField,
} from "../../../api/servicios";
import type { ServicePatchRequest, ValueWithUnit } from "../../../types/servicios.types";
import { ModalidadPicker } from "../ModalidadPicker";
import { RungPicker, type OfferValueLevel as RungValueLevel } from "../RungPicker";
import { VariantsRepeater } from "../VariantsRepeater";
import { NumberWithUnit } from "@/components/shared/NumberWithUnit";

// ── Schema ────────────────────────────────────────────────────────────────────

const resumenSchema = z.object({
  public_name: z.string().min(1, "El nombre es requerido"),
  category: z.string().nullable().optional(),
  modality: z.enum(["unica", "sesiones", "recurrente"]),
  appointment_type: z.string().nullable().optional(),
  // Rich text fields — G2-F11: migrated to RHF local state (ADR-009 §2.1)
  description_long: z.string().nullable().optional(),
  includes: z.string().nullable().optional(),
  excludes: z.string().nullable().optional(),
  warranty: z.string().nullable().optional(),
  procedure_steps: z.string().nullable().optional(),
  anesthesia_pain: z.string().nullable().optional(),
  prep: z.string().nullable().optional(),
  aftercare: z.string().nullable().optional(),
  downtime: z.string().nullable().optional(),
  expected_result: z.string().nullable().optional(),
  result_timing: z.string().nullable().optional(),
  result_lifespan: z.string().nullable().optional(),
  realistic_expectations: z.string().nullable().optional(),
  risks: z.string().nullable().optional(),
  red_flags: z.string().nullable().optional(),
});

type ResumenFormValues = z.infer<typeof resumenSchema>;

// ── Tipo de cita options (RN-32 · canonical Select enum) ─────────────────────

const APPOINTMENT_TYPE_OPTIONS = [
  {
    value: "primera_visita",
    label: "Primera visita",
    description: "El paciente nunca ha recibido este tratamiento",
  },
  {
    value: "control",
    label: "Control / seguimiento",
    description: "Consulta de revisión posterior al tratamiento",
  },
  {
    value: "valoracion",
    label: "Valoración",
    description: "Evaluación previa para candidatura al tratamiento",
  },
  {
    value: "procedimiento",
    label: "Procedimiento",
    description: "Sesión directa del tratamiento",
  },
  {
    value: "urgencia",
    label: "Urgencia / emergencia",
    description: "Atención no programada por dolor o complicación",
  },
];

// ── Interval unit options ─────────────────────────────────────────────────────

type IntervalUnit = ValueWithUnit["unit"];

const INTERVAL_UNITS: { value: IntervalUnit; label: string }[] = [
  { value: "dias", label: "días" },
  { value: "semanas", label: "semanas" },
  { value: "meses", label: "meses" },
  { value: "anios", label: "años" },
];

// ── Component ─────────────────────────────────────────────────────────────────

interface ResumenViewProps {
  offerId: string;
}

export function ResumenView({ offerId }: ResumenViewProps) {
  const { data: servicio } = useServicioDetail({ offerId });
  const { mutateAsync: patchFieldAsync } = usePatchField(offerId);

  const saveFn = useCallback(
    (patch: ServicePatchRequest) => patchFieldAsync(patch),
    [patchFieldAsync],
  );

  const { schedule, status } = useAutosave<ServicePatchRequest>({ saveFn });

  const form = useForm<ResumenFormValues>({
    resolver: zodResolver(resumenSchema),
    defaultValues: {
      public_name: servicio?.public_name ?? "",
      category: servicio?.category ?? null,
      modality: (servicio?.modality as ResumenFormValues["modality"]) ?? "unica",
      appointment_type: servicio?.initial_appt_type ?? null,
      // Rich text fields — G2-F11 (ADR-009 §2.1)
      description_long: servicio?.description_long ?? null,
      includes: servicio?.includes ?? null,
      excludes: servicio?.excludes ?? null,
      warranty: servicio?.warranty ?? null,
      procedure_steps: servicio?.procedure_steps ?? null,
      anesthesia_pain: servicio?.anesthesia_pain ?? null,
      prep: servicio?.prep ?? null,
      aftercare: servicio?.aftercare ?? null,
      downtime: servicio?.downtime ?? null,
      expected_result: servicio?.expected_result ?? null,
      result_timing: servicio?.result_timing ?? null,
      result_lifespan: servicio?.result_lifespan ?? null,
      realistic_expectations: servicio?.realistic_expectations ?? null,
      risks: servicio?.risks ?? null,
      red_flags: servicio?.red_flags ?? null,
    },
  });

  // Reset form when servicio entity changes (SSR hydration guard)
  useEffect(() => {
    if (servicio) {
      form.reset({
        public_name: servicio.public_name ?? "",
        category: servicio.category ?? null,
        modality: (servicio.modality as ResumenFormValues["modality"]) ?? "unica",
        appointment_type: servicio.initial_appt_type ?? null,
        // Rich text fields — G2-F11 (ADR-009 §2.1)
        description_long: servicio.description_long ?? null,
        includes: servicio.includes ?? null,
        excludes: servicio.excludes ?? null,
        warranty: servicio.warranty ?? null,
        procedure_steps: servicio.procedure_steps ?? null,
        anesthesia_pain: servicio.anesthesia_pain ?? null,
        prep: servicio.prep ?? null,
        aftercare: servicio.aftercare ?? null,
        downtime: servicio.downtime ?? null,
        expected_result: servicio.expected_result ?? null,
        result_timing: servicio.result_timing ?? null,
        result_lifespan: servicio.result_lifespan ?? null,
        realistic_expectations: servicio.realistic_expectations ?? null,
        risks: servicio.risks ?? null,
        red_flags: servicio.red_flags ?? null,
      });
    }
    // Reset only when a different entity loads (offer_id signals entity switch;
    // form/servicio intentionally excluded to avoid clobbering in-progress autosave)
  }, [servicio?.offer_id]); // intentional: exclude form from deps — see comment

  const isEstandar = !!servicio?.canonical_service_ref;

  // Modality watch drives conditional reveal of interval fields (C.2.3)
  const modality = form.watch("modality");

  if (!servicio) {
    return (
      <div className="p-6 space-y-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-20 bg-muted rounded-md animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="p-5 md:p-6 space-y-6 pb-24">

      {/* ── Grupo 1: Identidad (defaultOpen) ──────────────────────────────── */}
      <CollapsibleSection
        title="Identidad"
        defaultOpen
        accentVar="--agent-lisa"
        summary="3 campos"
      >
        <div className="space-y-4 pt-1">
          <div className="space-y-2">
            <Label htmlFor="public_name">Nombre del servicio</Label>
            <Controller
              control={form.control}
              name="public_name"
              render={({ field, fieldState }) => (
                <>
                  <Input
                    id="public_name"
                    {...field}
                    placeholder="Ej. Diseño de sonrisa"
                    className={fieldState.error ? "border-destructive" : ""}
                    onChange={(e) => {
                      field.onChange(e);
                      schedule({ public_name: e.target.value });
                    }}
                  />
                  {fieldState.error && (
                    <p className="text-sm text-destructive">{fieldState.error.message}</p>
                  )}
                </>
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="category">
              Categoría / especialidad
              {isEstandar && (
                <span className="ml-2 text-xs text-muted-foreground">(heredada del estándar)</span>
              )}
            </Label>
            <Controller
              control={form.control}
              name="category"
              render={({ field }) => (
                <Input
                  id="category"
                  value={field.value ?? ""}
                  onChange={(e) => {
                    const v = e.target.value || null;
                    field.onChange(v);
                    if (!isEstandar) {
                      schedule({ category: v });
                    }
                  }}
                  placeholder="Ej. Odontología estética"
                  disabled={isEstandar}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label>Peldaño de valor</Label>
            <RungPicker
              value={
                (servicio.value_level ?? "transformacion").toUpperCase() as RungValueLevel
              }
              onChange={() => {
                // value_level PATCH gap — see T-6-impl-log.md § Upstream deficiency
              }}
              locked={isEstandar}
            />
          </div>
        </div>
      </CollapsibleSection>

      {/* ── Grupo 2: Qué es ────────────────────────────────────────────────── */}
      <CollapsibleSection
        title="Qué es"
        accentVar="--agent-lisa"
        summary="5 campos"
      >
        <div className="space-y-4 pt-1">
          <div className="space-y-2">
            <Label htmlFor="description_long">
              Descripción corta{" "}
              <span className="text-xs text-muted-foreground">(lenguaje del paciente)</span>
            </Label>
            <Controller
              control={form.control}
              name="description_long"
              render={({ field }) => (
                <Textarea
                  id="description_long"
                  value={field.value ?? ""}
                  placeholder="Una frase que el paciente entiende al instante"
                  rows={2}
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ description_long: e.target.value || null });
                  }}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="includes">Qué incluye</Label>
            <Controller
              control={form.control}
              name="includes"
              render={({ field }) => (
                <Textarea
                  id="includes"
                  value={field.value ?? ""}
                  placeholder="Lista lo que está incluido en el precio…"
                  rows={3}
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ includes: e.target.value || null });
                  }}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="excludes">Qué no incluye</Label>
            <Controller
              control={form.control}
              name="excludes"
              render={({ field }) => (
                <Textarea
                  id="excludes"
                  value={field.value ?? ""}
                  placeholder="Lo que el paciente debe conseguir por su cuenta…"
                  rows={2}
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ excludes: e.target.value || null });
                  }}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="warranty">Garantía</Label>
            <Controller
              control={form.control}
              name="warranty"
              render={({ field }) => (
                <Textarea
                  id="warranty"
                  value={field.value ?? ""}
                  placeholder="Condiciones de la garantía o política de re-tratamiento…"
                  rows={2}
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ warranty: e.target.value || null });
                  }}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label>Variantes del servicio</Label>
            <VariantsRepeater
              value={servicio.variants ?? []}
              onChange={(variants) => schedule({ variants })}
              // Canon currency rule: NEVER ?? "USD"; pass undefined when null
              currency={servicio.currency ?? undefined}
            />
          </div>
        </div>
      </CollapsibleSection>

      {/* ── Grupo 3: El procedimiento ───────────────────────────────────────── */}
      <CollapsibleSection
        title="El procedimiento"
        accentVar="--agent-lisa"
        summary="5 campos"
      >
        <div className="space-y-4 pt-1">
          <div className="space-y-2">
            <Label htmlFor="procedure_steps">Cómo se hace</Label>
            <Controller
              control={form.control}
              name="procedure_steps"
              render={({ field }) => (
                <Textarea
                  id="procedure_steps"
                  value={field.value ?? ""}
                  placeholder="Pasos que vive el paciente, en lenguaje claro…"
                  rows={4}
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ procedure_steps: e.target.value || null });
                  }}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="anesthesia_pain">Anestesia y dolor</Label>
            <Controller
              control={form.control}
              name="anesthesia_pain"
              render={({ field }) => (
                <Textarea
                  id="anesthesia_pain"
                  value={field.value ?? ""}
                  placeholder="Nivel de dolor esperado y qué anestesia se usa…"
                  rows={2}
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ anesthesia_pain: e.target.value || null });
                  }}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="prep">Preparación previa</Label>
            <Controller
              control={form.control}
              name="prep"
              render={({ field }) => (
                <Textarea
                  id="prep"
                  value={field.value ?? ""}
                  placeholder="Qué debe hacer el paciente antes de la cita…"
                  rows={2}
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ prep: e.target.value || null });
                  }}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="aftercare">Cuidados posteriores</Label>
            <Controller
              control={form.control}
              name="aftercare"
              render={({ field }) => (
                <Textarea
                  id="aftercare"
                  value={field.value ?? ""}
                  placeholder="Qué debe hacer y evitar el paciente luego…"
                  rows={2}
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ aftercare: e.target.value || null });
                  }}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="downtime">Tiempo de recuperación</Label>
            <Controller
              control={form.control}
              name="downtime"
              render={({ field }) => (
                <Textarea
                  id="downtime"
                  value={field.value ?? ""}
                  placeholder="Días de reposo o restricciones de actividad…"
                  rows={2}
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ downtime: e.target.value || null });
                  }}
                />
              )}
            />
          </div>
        </div>
      </CollapsibleSection>

      {/* ── Grupo 4: Resultados ─────────────────────────────────────────────── */}
      <CollapsibleSection
        title="Resultados"
        accentVar="--agent-lisa"
        summary="4 campos"
      >
        <div className="space-y-4 pt-1">
          <div className="space-y-2">
            <Label htmlFor="expected_result">Resultado esperado</Label>
            <Controller
              control={form.control}
              name="expected_result"
              render={({ field }) => (
                <Textarea
                  id="expected_result"
                  value={field.value ?? ""}
                  placeholder="El cambio visible/tangible que experimenta el paciente…"
                  rows={2}
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ expected_result: e.target.value || null });
                  }}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="result_timing">¿Cuándo se ve el resultado?</Label>
            <Controller
              control={form.control}
              name="result_timing"
              render={({ field }) => (
                <Input
                  id="result_timing"
                  value={field.value ?? ""}
                  placeholder="Ej. A las 48h se aprecian los primeros resultados"
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ result_timing: e.target.value || null });
                  }}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="result_lifespan">Duración del resultado</Label>
            <Controller
              control={form.control}
              name="result_lifespan"
              render={({ field }) => (
                <Input
                  id="result_lifespan"
                  value={field.value ?? ""}
                  placeholder="Ej. 2 años con mantenimiento adecuado"
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ result_lifespan: e.target.value || null });
                  }}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="realistic_expectations">Expectativas realistas</Label>
            <Controller
              control={form.control}
              name="realistic_expectations"
              render={({ field }) => (
                <Textarea
                  id="realistic_expectations"
                  value={field.value ?? ""}
                  placeholder="Qué puede y qué no puede esperar el paciente…"
                  rows={2}
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ realistic_expectations: e.target.value || null });
                  }}
                />
              )}
            />
          </div>
        </div>
      </CollapsibleSection>

      {/* ── Grupo 5: Riesgos ────────────────────────────────────────────────── */}
      <CollapsibleSection
        title="Riesgos"
        accentVar="--agent-lisa"
        summary="2 campos"
      >
        <div className="space-y-4 pt-1">
          <div className="space-y-2">
            <Label htmlFor="risks">Riesgos y efectos secundarios</Label>
            <Controller
              control={form.control}
              name="risks"
              render={({ field }) => (
                <Textarea
                  id="risks"
                  value={field.value ?? ""}
                  placeholder="Señala los riesgos reales (curados, no alarmistas)…"
                  rows={3}
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ risks: e.target.value || null });
                  }}
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="red_flags">Señales de alarma</Label>
            <Controller
              control={form.control}
              name="red_flags"
              render={({ field }) => (
                <Textarea
                  id="red_flags"
                  value={field.value ?? ""}
                  placeholder="Si pasa X, el paciente debe llamar a la clínica…"
                  rows={2}
                  onChange={(e) => {
                    field.onChange(e);
                    schedule({ red_flags: e.target.value || null });
                  }}
                />
              )}
            />
          </div>
        </div>
      </CollapsibleSection>

      {/* ── Grupo 6: Modalidad y agenda ─────────────────────────────────────── */}
      <CollapsibleSection
        title="Modalidad y agenda"
        accentVar="--agent-lisa"
        summary="4 campos"
      >
        <div className="space-y-4 pt-1">
          <div className="space-y-2">
            <Label>Modalidad</Label>
            <Controller
              control={form.control}
              name="modality"
              render={({ field }) => (
                <ModalidadPicker
                  value={field.value}
                  onChange={(v) => {
                    field.onChange(v);
                    schedule({ modality: v });
                  }}
                />
              )}
            />
          </div>

          {/* Conditional: session_interval — only when modality=sesiones (C.2.3) */}
          {modality === "sesiones" && (
            <div className="space-y-2">
              <Label>Intervalo entre sesiones</Label>
              <div className="flex gap-2">
                <NumberWithUnit
                  value={servicio.session_interval?.value ?? 1}
                  onChange={(v) =>
                    schedule({
                      session_interval: {
                        value: v,
                        unit: servicio.session_interval?.unit ?? "semanas",
                      },
                    })
                  }
                  unit="sesiones"
                  min={1}
                  step={1}
                  placeholder="1"
                />
                <Select
                  value={servicio.session_interval?.unit ?? "semanas"}
                  onValueChange={(unit) =>
                    schedule({
                      session_interval: {
                        value: servicio.session_interval?.value ?? 1,
                        unit: unit as IntervalUnit,
                      },
                    })
                  }
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {INTERVAL_UNITS.map((u) => (
                      <SelectItem key={u.value} value={u.value}>
                        {u.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          {/* Conditional: recurrence_interval — only when modality=recurrente (C.2.3) */}
          {modality === "recurrente" && (
            <div className="space-y-2">
              <Label>Intervalo de recurrencia</Label>
              <div className="flex gap-2">
                <NumberWithUnit
                  value={servicio.recurrence_interval?.value ?? 1}
                  onChange={(v) =>
                    schedule({
                      recurrence_interval: {
                        value: v,
                        unit: servicio.recurrence_interval?.unit ?? "meses",
                      },
                    })
                  }
                  unit="cada"
                  min={1}
                  step={1}
                  placeholder="1"
                />
                <Select
                  value={servicio.recurrence_interval?.unit ?? "meses"}
                  onValueChange={(unit) =>
                    schedule({
                      recurrence_interval: {
                        value: servicio.recurrence_interval?.value ?? 1,
                        unit: unit as IntervalUnit,
                      },
                    })
                  }
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {INTERVAL_UNITS.map((u) => (
                      <SelectItem key={u.value} value={u.value}>
                        {u.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="initial_appt_duration">Duración de la cita inicial</Label>
            <NumberWithUnit
              value={servicio.initial_appt_duration_minutes ?? 30}
              onChange={(v) => schedule({ initial_appt_duration_minutes: v })}
              unit="min"
              min={1}
              step={5}
              placeholder="45"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="appointment_type">Tipo de cita inicial</Label>
            <Controller
              control={form.control}
              name="appointment_type"
              render={({ field }) => (
                // ponytail: plain Select (not ui-kit RichSelect) — RichSelect hard-renders
                // <FormControl>/useFormContext, which crashes outside a shadcn <Form> stack;
                // this leaf uses bare Controller. Same label+description UI, no form context.
                <Select
                  value={field.value ?? undefined}
                  onValueChange={(v) => {
                    field.onChange(v);
                    schedule({ initial_appt_type: v });
                  }}
                >
                  <SelectTrigger className="h-auto py-3 text-left">
                    <SelectValue placeholder="Selecciona el tipo de cita…" />
                  </SelectTrigger>
                  <SelectContent>
                    {APPOINTMENT_TYPE_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value} className="py-3">
                        <div className="flex flex-col items-start gap-1 text-left">
                          <span className="font-medium">{option.label}</span>
                          {option.description && (
                            <span className="text-xs text-muted-foreground whitespace-normal leading-tight">
                              {option.description}
                            </span>
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>
        </div>
      </CollapsibleSection>

      {/* Autosave indicator — ONE per page (canon §2.6) */}
      <FloatingAutosaveIndicator status={status} />
    </div>
  );
}
