// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
"use client";
/**
 * StructuredProfileEditor.tsx — RHF+Zod form for structured public profile fields.
 *
 * Sections (per mockup D3-D):
 *   - Sobre mí (textarea, freeform)
 *   - Formación (array ≥ 4 fields → split by form-runtime default)
 *   - Experiencia (array ≥ 4 fields → split)
 *   - Tratamientos (string[] — tag chips)
 *   - Certificaciones (array ≥ 3 fields → cards)
 *   - Idiomas (array ≤ 2 fields → cards)
 *
 * Autosave: 600ms coalescing (use-autosave). Emits status via onAutosaveStatusChange.
 * canon §2.6: FloatingAutosaveIndicator singleton lives in DoctorPaginaView (W4 fix).
 *
 * T-FE-pagina-publica vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-D.3
 */

import { useEffect, useCallback, useRef } from "react";
import { useForm, useFieldArray, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useSavePublicProfile } from "../../../../api/staff";
import { useAutosave } from "@/hooks/use-autosave";
// FloatingAutosaveIndicator moved to DoctorPaginaView (W4)
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { DoctorDetail, SavePublicProfilePayload } from "../../../../api/staff";

// ── Zod schema ────────────────────────────────────────────────────────────────

const formacionSchema = z.object({
  titulo: z.string().min(1, "Requerido"),
  institucion: z.string().optional(),
  anio: z.union([z.number().int().min(1900).max(2100), z.null()]).optional(),
});

// experienciaSchema — real BE wire shape (commit 275d5d7e, finding F2)
// {puesto, lugar, anios} — NOT {cargo, institucion, desde, hasta, descripcion}
const experienciaSchema = z.object({
  puesto: z.string().min(1, "Requerido"),
  lugar: z.string().optional(),
  anios: z.union([z.number().int().min(0).max(60), z.null()]).optional(),
});

// certificaciones + idiomas are string[] on the wire (finding F3)
// Form stores them as {_value: string} wrapper for useFieldArray compatibility
const certificacionItemSchema = z.object({ _value: z.string().min(1, "Requerido") });
const idiomaItemSchema = z.object({ _value: z.string().min(1, "Requerido") });

const publicProfileSchema = z.object({
  sobreMi: z.string().max(2000, "Máximo 2000 caracteres").optional(),
  formacion: z.array(formacionSchema),
  experiencia: z.array(experienciaSchema),
  tratamientosRaw: z.string().max(1000, "Máximo 1000 caracteres").optional(),
  certificaciones: z.array(certificacionItemSchema),
  idiomas: z.array(idiomaItemSchema),
});

type PublicProfileFormValues = z.infer<typeof publicProfileSchema>;

interface StructuredProfileEditorProps {
  doctorId: string;
  doctor: DoctorDetail;
  /** W4: callback to lift autosave status to DoctorPaginaView's singleton FloatingAutosaveIndicator */
  onAutosaveStatusChange?: (status: import("@/hooks/use-autosave").AutosaveStatus) => void;
}

// ── Sub-section card wrapper ──────────────────────────────────────────────────

function SectionCard({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      aria-labelledby={`section-${label.replace(/\s+/g, "-").toLowerCase()}`}
      className={cn(
        "rounded-xl border border-border bg-card p-4",
        className,
      )}
    >
      <h3
        id={`section-${label.replace(/\s+/g, "-").toLowerCase()}`}
        className="mb-3 flex items-center gap-2 text-sm font-semibold"
      >
        <span aria-hidden="true" className="h-4 w-1 rounded-full bg-agent-lisa shrink-0" />
        {label}
      </h3>
      {children}
    </section>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

/**
 * StructuredProfileEditor — autosave form for public profile structured fields.
 */
export function StructuredProfileEditor({ doctorId, doctor, onAutosaveStatusChange }: StructuredProfileEditorProps) {
  const saveMutation = useSavePublicProfile(doctorId);

  const form = useForm<PublicProfileFormValues>({
    resolver: zodResolver(publicProfileSchema),
    defaultValues: {
      sobreMi: "",
      formacion: [],
      experiencia: [],
      tratamientosRaw: "",
      certificaciones: [],
      idiomas: [],
    },
  });

  // Hydrate from doctor.publicProfile when data loads.
  // Shapes per real BE DTO (commit 275d5d7e — findings F2/F3):
  //   experiencia: [{puesto, lugar, anios}] (NOT cargo/institucion/desde/hasta)
  //   certificaciones: string[] → wrap as {_value} for useFieldArray
  //   idiomas: string[] → wrap as {_value} for useFieldArray
  useEffect(() => {
    if (doctor.publicProfile != null) {
      form.reset({
        sobreMi: doctor.publicProfile.sobreMi ?? "",
        formacion: (doctor.publicProfile.formacion ?? []).map((f) => ({
          titulo: f.titulo,
          institucion: f.institucion ?? undefined,
          anio: f.anio ?? null,
        })),
        experiencia: (doctor.publicProfile.experiencia ?? []).map((e) => ({
          puesto: e.puesto,
          lugar: e.lugar ?? undefined,
          anios: e.anios ?? null,
        })),
        tratamientosRaw: (doctor.publicProfile.tratamientos ?? []).join(", "),
        certificaciones: (doctor.publicProfile.certificaciones ?? []).map((c) => ({
          _value: c,
        })),
        idiomas: (doctor.publicProfile.idiomas ?? []).map((lang) => ({
          _value: lang,
        })),
      });
    }
  }, [doctor.publicProfile, form]);

  // Field arrays
  const formacionFields = useFieldArray({ control: form.control, name: "formacion" });
  const experienciaFields = useFieldArray({ control: form.control, name: "experiencia" });
  const certificacionFields = useFieldArray({ control: form.control, name: "certificaciones" });
  const idiomaFields = useFieldArray({ control: form.control, name: "idiomas" });

  // ── Autosave (600ms coalescing) — emit status to page-level singleton (W4) ──
  const { schedule: scheduleAutosave, status: autosaveStatus } = useAutosave({
    saveFn: async (payload: SavePublicProfilePayload) => {
      await saveMutation.mutateAsync(payload);
    },
    debounceMs: 600,
  });

  // Stable ref for onAutosaveStatusChange to avoid stale closure in effect
  const onStatusChangeRef = useRef(onAutosaveStatusChange);
  onStatusChangeRef.current = onAutosaveStatusChange;

  useEffect(() => {
    onStatusChangeRef.current?.(autosaveStatus);
  }, [autosaveStatus]);

  // buildPayload — shapes per real BE DTO (commit 275d5d7e — findings F2/F3)
  const buildPayload = useCallback((): SavePublicProfilePayload => {
    const vals = form.getValues();
    return {
      sobreMi: vals.sobreMi || null,
      formacion: vals.formacion.map((f) => ({
        titulo: f.titulo,
        institucion: f.institucion || "",
        anio: f.anio ?? null,
      })),
      experiencia: vals.experiencia.map((e) => ({
        puesto: e.puesto,
        lugar: e.lugar || "",
        anios: e.anios ?? null,
      })),
      tratamientos: (vals.tratamientosRaw ?? "")
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
      // Unwrap {_value} wrapper → string[]
      certificaciones: vals.certificaciones
        .map((c) => c._value.trim())
        .filter(Boolean),
      idiomas: vals.idiomas
        .map((i) => i._value.trim())
        .filter(Boolean),
    };
  }, [form]);

  const handleChange = useCallback(() => {
    scheduleAutosave(buildPayload());
  }, [scheduleAutosave, buildPayload]);

  // ── Loading skeleton ───────────────────────────────────────────────────
  if (!doctor.publicProfile && !form.formState.isDirty) {
    // Show only skeletons before first generation — user sees CTA in DoctorPaginaView
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full rounded-xl" />
        <Skeleton className="h-24 w-full rounded-xl" />
        <p className="text-xs text-center text-muted-foreground">
          Genera el perfil para empezar a editar los campos.
        </p>
      </div>
    );
  }

  return (
    <section className="flex flex-col gap-4" aria-label="Editor de perfil estructurado" data-testid="structured-profile-editor">
      {/* Sobre mí */}
      <SectionCard label="Sobre mí">
        <Controller
          control={form.control}
          name="sobreMi"
          render={({ field, fieldState }) => (
            <div className="space-y-1">
              <Label htmlFor="sobreMi" className="sr-only">Sobre mí</Label>
              <Textarea
                id="sobreMi"
                placeholder="Presentación profesional del doctor..."
                rows={5}
                aria-invalid={!!fieldState.error}
                {...field}
                onChange={(e) => {
                  field.onChange(e);
                  handleChange();
                }}
              />
              {fieldState.error && (
                <p className="text-xs text-destructive" role="alert">
                  {fieldState.error.message}
                </p>
              )}
            </div>
          )}
        />
      </SectionCard>

      {/* Formación */}
      <SectionCard label="Formación">
        <div className="space-y-3">
          {formacionFields.fields.map((field, idx) => (
            <fieldset
              key={field.id}
              className="grid grid-cols-1 gap-2 rounded-lg border border-border/50 p-3 sm:grid-cols-2 [border:none] border"
            >
              <Controller
                control={form.control}
                name={`formacion.${idx}.titulo`}
                render={({ field: f, fieldState }) => (
                  <div className="space-y-1 sm:col-span-2">
                    <Label htmlFor={`formacion-${idx}-titulo`}>Título / Grado</Label>
                    <Input
                      id={`formacion-${idx}-titulo`}
                      placeholder="Ej. Médico cirujano"
                      aria-invalid={!!fieldState.error}
                      {...f}
                      onChange={(e) => { f.onChange(e); handleChange(); }}
                    />
                    {fieldState.error && (
                      <p className="text-xs text-destructive" role="alert">{fieldState.error.message}</p>
                    )}
                  </div>
                )}
              />
              <Controller
                control={form.control}
                name={`formacion.${idx}.institucion`}
                render={({ field: f }) => (
                  <div className="space-y-1">
                    <Label htmlFor={`formacion-${idx}-inst`}>Institución</Label>
                    <Input
                      id={`formacion-${idx}-inst`}
                      placeholder="Ej. UPCH"
                      {...f}
                      onChange={(e) => { f.onChange(e); handleChange(); }}
                    />
                  </div>
                )}
              />
              <Controller
                control={form.control}
                name={`formacion.${idx}.anio`}
                render={({ field: f }) => (
                  <div className="space-y-1">
                    <Label htmlFor={`formacion-${idx}-anio`}>Año</Label>
                    <Input
                      id={`formacion-${idx}-anio`}
                      type="number"
                      min={1950}
                      max={2100}
                      placeholder="2020"
                      value={f.value ?? ""}
                      onChange={(e) => {
                        const v = e.target.value ? parseInt(e.target.value, 10) : null;
                        f.onChange(v);
                        handleChange();
                      }}
                    />
                  </div>
                )}
              />
              <div className="sm:col-span-2 flex justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs text-muted-foreground hover:text-destructive"
                  onClick={() => { formacionFields.remove(idx); handleChange(); }}
                  aria-label={`Eliminar formación ${idx + 1}`}
                >
                  Eliminar
                </Button>
              </div>
            </fieldset>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="w-full text-xs"
            onClick={() => {
              formacionFields.append({ titulo: "", institucion: "", anio: null });
            }}
            aria-label="Agregar formación académica"
          >
            + Agregar formación
          </Button>
        </div>
      </SectionCard>

      {/* Experiencia — fields per real BE DTO: puesto/lugar/anios (finding F2) */}
      <SectionCard label="Experiencia">
        <div className="space-y-3">
          {experienciaFields.fields.map((field, idx) => (
            <fieldset
              key={field.id}
              className="grid grid-cols-1 gap-2 rounded-lg border border-border/50 p-3 sm:grid-cols-2"
            >
              <Controller
                control={form.control}
                name={`experiencia.${idx}.puesto`}
                render={({ field: f, fieldState }) => (
                  <div className="space-y-1 sm:col-span-2">
                    <Label htmlFor={`exp-${idx}-puesto`}>Puesto / Cargo</Label>
                    <Input
                      id={`exp-${idx}-puesto`}
                      placeholder="Ej. Odontólogo de planta"
                      aria-invalid={!!fieldState.error}
                      {...f}
                      onChange={(e) => { f.onChange(e); handleChange(); }}
                    />
                    {fieldState.error && (
                      <p className="text-xs text-destructive" role="alert">{fieldState.error.message}</p>
                    )}
                  </div>
                )}
              />
              <Controller
                control={form.control}
                name={`experiencia.${idx}.lugar`}
                render={({ field: f }) => (
                  <div className="space-y-1">
                    <Label htmlFor={`exp-${idx}-lugar`}>Lugar / Institución</Label>
                    <Input
                      id={`exp-${idx}-lugar`}
                      placeholder="Ej. Hospital Rebagliati"
                      {...f}
                      value={f.value ?? ""}
                      onChange={(e) => { f.onChange(e); handleChange(); }}
                    />
                  </div>
                )}
              />
              <Controller
                control={form.control}
                name={`experiencia.${idx}.anios`}
                render={({ field: f }) => (
                  <div className="space-y-1">
                    <Label htmlFor={`exp-${idx}-anios`}>Años de experiencia</Label>
                    <Input
                      id={`exp-${idx}-anios`}
                      type="number"
                      min={0}
                      max={60}
                      placeholder="5"
                      value={f.value ?? ""}
                      onChange={(e) => {
                        const v = e.target.value ? parseInt(e.target.value, 10) : null;
                        f.onChange(v);
                        handleChange();
                      }}
                    />
                  </div>
                )}
              />
              <div className="sm:col-span-2 flex justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs text-muted-foreground hover:text-destructive"
                  onClick={() => { experienciaFields.remove(idx); handleChange(); }}
                  aria-label={`Eliminar experiencia ${idx + 1}`}
                >
                  Eliminar
                </Button>
              </div>
            </fieldset>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="w-full text-xs"
            onClick={() => {
              experienciaFields.append({ puesto: "", lugar: "", anios: null });
            }}
            aria-label="Agregar experiencia profesional"
          >
            + Agregar experiencia
          </Button>
        </div>
      </SectionCard>

      {/* Tratamientos */}
      <SectionCard label="Tratamientos">
        <Controller
          control={form.control}
          name="tratamientosRaw"
          render={({ field, fieldState }) => (
            <div className="space-y-1">
              <Label htmlFor="tratamientos">Tratamientos (separados por coma)</Label>
              <Input
                id="tratamientos"
                placeholder="Ej. Carillas, Blanqueamiento, Implantes"
                aria-invalid={!!fieldState.error}
                {...field}
                onChange={(e) => { field.onChange(e); handleChange(); }}
              />
              {/* Chip preview */}
              {field.value && (
                <div className="flex flex-wrap gap-1.5 mt-2" aria-label="Tratamientos">
                  {field.value
                    .split(",")
                    .map((t) => t.trim())
                    .filter(Boolean)
                    .map((t) => (
                      <span
                        key={t}
                        className="inline-flex items-center rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium"
                      >
                        {t}
                      </span>
                    ))}
                </div>
              )}
              {fieldState.error && (
                <p className="text-xs text-destructive" role="alert">{fieldState.error.message}</p>
              )}
            </div>
          )}
        />
      </SectionCard>

      {/* Certificaciones — string[] on wire (finding F3); UI uses {_value} wrapper */}
      <SectionCard label="Certificaciones">
        <div className="space-y-2">
          {certificacionFields.fields.map((field, idx) => (
            <div key={field.id} className="flex gap-2 items-start">
              <Controller
                control={form.control}
                name={`certificaciones.${idx}._value`}
                render={({ field: f, fieldState }) => (
                  <div className="flex-1 space-y-1">
                    <Input
                      id={`cert-${idx}`}
                      placeholder="Ej. Colegiatura 12345 (PE)"
                      aria-label={`Certificación ${idx + 1}`}
                      aria-invalid={!!fieldState.error}
                      {...f}
                      onChange={(e) => { f.onChange(e); handleChange(); }}
                    />
                    {fieldState.error && (
                      <p className="text-xs text-destructive" role="alert">{fieldState.error.message}</p>
                    )}
                  </div>
                )}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-9 shrink-0 text-xs text-muted-foreground hover:text-destructive"
                onClick={() => { certificacionFields.remove(idx); handleChange(); }}
                aria-label={`Eliminar certificación ${idx + 1}`}
              >
                ✕
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="w-full text-xs"
            onClick={() => {
              certificacionFields.append({ _value: "" });
            }}
            aria-label="Agregar certificación"
          >
            + Agregar certificación
          </Button>
        </div>
      </SectionCard>

      {/* Idiomas — string[] on wire (finding F3); UI uses {_value} wrapper */}
      <SectionCard label="Idiomas">
        <div className="space-y-2">
          {idiomaFields.fields.map((field, idx) => (
            <div key={field.id} className="flex gap-2 items-start">
              <Controller
                control={form.control}
                name={`idiomas.${idx}._value`}
                render={({ field: f, fieldState }) => (
                  <div className="flex-1 space-y-1">
                    <Input
                      id={`idioma-${idx}`}
                      placeholder="Ej. Inglés intermedio"
                      aria-label={`Idioma ${idx + 1}`}
                      aria-invalid={!!fieldState.error}
                      {...f}
                      onChange={(e) => { f.onChange(e); handleChange(); }}
                    />
                    {fieldState.error && (
                      <p className="text-xs text-destructive" role="alert">{fieldState.error.message}</p>
                    )}
                  </div>
                )}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-9 shrink-0 text-xs text-muted-foreground hover:text-destructive"
                onClick={() => { idiomaFields.remove(idx); handleChange(); }}
                aria-label={`Eliminar idioma ${idx + 1}`}
              >
                ✕
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="w-full text-xs"
            onClick={() => idiomaFields.append({ _value: "" })}
            aria-label="Agregar idioma"
          >
            + Agregar idioma
          </Button>
        </div>
      </SectionCard>

      {/* FloatingAutosaveIndicator moved to DoctorPaginaView (W4 — combines BioRepoInputs +
           StructuredProfileEditor statuses in ONE indicator per canon §2.6) */}
    </section>
  );
}
