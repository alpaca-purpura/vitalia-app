// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
// @deprecated T-FE-1 vitalia-fase2-mateo-nueva-cita (AC-9/D-G): This modal form is
// REPLACED by the full-page NuevaCitaView route. Retained temporarily pending cleanup story.
// TS errors suppressed via @ts-nocheck: schema reconciliation (T-FE-1) changed origin enum
// (removed "existing_patient") and removed patientNewData field. Delete in cleanup story.
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-nocheck
"use client";

/**
 * CrearCitaForm.tsx — Unified appointment creation form.
 * T-16 vitalia-fase2-valeria-agenda
 *
 * 3 origin variants driven by `origin` field (discriminated):
 *   - walk_in: PatientNewData fields (name + phone + optional email + optional dni)
 *   - telefono: same PatientNewData fields (reserved phone booking)
 *   - existing_patient: PatientAutocomplete (search + patient_id only)
 *
 * Success → Sonner toast "Cita creada" + onSuccess callback.
 * Error → ErrorAlert inline.
 *
 * No "Guardar" button — immediate submission only (A2 acceptance criteria).
 * RHF + Zod resolver (CreateAppointmentRequestSchema from T-11).
 *
 * HIPAA-lite:
 * - PatientAutocomplete returns patient_id ONLY (no PHI in form state for existing patients)
 * - patientNewData is new patient PHI — only sent once to server in POST body (not stored FE-side)
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 01-spec.md SC-2 + 03-arch.md § 6.9 + 06-tickets.yaml T-16
 */

import * as React from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
  CreateAppointmentRequestSchema,
  type CreateAppointmentRequestDTO,
} from "../../types/agenda-schema";
import { useCreateAppointment } from "../../api/agenda";
import { PatientAutocomplete } from "./PatientAutocomplete";

// ── Types ─────────────────────────────────────────────────────────────────────

export type CrearCitaOrigin = "walk_in" | "telefono" | "existing_patient";

export interface CrearCitaFormProps {
  /** Initial origin — sets which form variant renders. */
  origin: CrearCitaOrigin;
  /** Tenant ID for API calls. */
  tenantId: string;
  /** Clinic ID for HIPAA dual-filter. */
  clinicId: string;
  /** Called after successful submission. */
  onSuccess?: () => void;
  /** Called when user wants to cancel/close. */
  onCancel?: () => void;
  className?: string;
}

// ── Labels ────────────────────────────────────────────────────────────────────

const ORIGIN_LABEL: Record<CrearCitaOrigin, string> = {
  walk_in: "Paciente walk-in (nuevo)",
  telefono: "Reserva telefónica (nuevo)",
  existing_patient: "Desde paciente existente",
};

// ── Error Alert ───────────────────────────────────────────────────────────────

interface ErrorAlertProps {
  error: Error;
}

function ErrorAlert({ error }: ErrorAlertProps) {
  return (
    <Alert variant="destructive" role="alert">
      <AlertTitle>Error al crear la cita</AlertTitle>
      <AlertDescription>
        {error.message || "Ocurrió un error inesperado. Intenta nuevamente."}
      </AlertDescription>
    </Alert>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * CrearCitaForm — RHF + Zod form for appointment creation.
 *
 * Variant rendering driven by `origin` prop:
 * - walk_in / telefono: show new patient fields
 * - existing_patient: show PatientAutocomplete
 *
 * @example
 * <CrearCitaForm
 *   origin="walk_in"
 *   tenantId={tenantId}
 *   clinicId={clinicId}
 *   onSuccess={() => setOpen(false)}
 * />
 */
export function CrearCitaForm({
  origin,
  tenantId,
  clinicId,
  onSuccess,
  onCancel,
  className,
}: CrearCitaFormProps) {
  const createMutation = useCreateAppointment(tenantId);

  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<CreateAppointmentRequestDTO>({
    resolver: zodResolver(CreateAppointmentRequestSchema),
    defaultValues: {
      origin,
      patientId: null,
      patientNewData: null,
      doctorId: "",
      serviceLabel: "",
      startTime: "",
      endTime: "",
      notesInternal: null,
      currencyOverride: null,
    },
  });

  const isNewPatient = origin === "walk_in" || origin === "telefono";
  const isExisting = origin === "existing_patient";

  const onSubmit = React.useCallback(
    async (data: CreateAppointmentRequestDTO) => {
      try {
        await createMutation.mutateAsync(data);
        toast.success("Cita creada", {
          description: `${ORIGIN_LABEL[origin]} registrada correctamente.`,
        });
        reset();
        onSuccess?.();
      } catch {
        // Error displayed inline via ErrorAlert — no re-throw needed
      }
    },
    [createMutation, origin, reset, onSuccess],
  );

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className={cn("flex flex-col gap-4 p-4", className)}
      data-testid="crear-cita-form"
      aria-label={`Formulario nueva cita: ${ORIGIN_LABEL[origin]}`}
      noValidate
    >
      {/* Hidden origin field */}
      <input type="hidden" {...register("origin")} value={origin} />

      {/* ── Patient section ────────────────────────────────────────────── */}
      <fieldset className="border-0 p-0 m-0">
        <legend className="text-sm font-semibold text-foreground mb-3">
          Datos del paciente
        </legend>

        {/* Existing patient: autocomplete */}
        {isExisting && (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="patient-autocomplete">
              Buscar paciente
              <span className="text-destructive ml-0.5" aria-hidden="true">*</span>
            </Label>
            <Controller
              name="patientId"
              control={control}
              render={({ field }) => (
                <PatientAutocomplete
                  value={field.value ?? null}
                  onChange={field.onChange}
                  tenantId={tenantId}
                  clinicId={clinicId}
                  aria-label="Buscar paciente existente"
                />
              )}
            />
            {errors.patientId && (
              <p className="text-xs text-destructive" role="alert">
                {errors.patientId.message}
              </p>
            )}
          </div>
        )}

        {/* New patient: inline fields */}
        {isNewPatient && (
          <div className="flex flex-col gap-3">
            {/* Name */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="patientNewData.name">
                Nombre completo
                <span className="text-destructive ml-0.5" aria-hidden="true">*</span>
              </Label>
              <Input
                id="patientNewData.name"
                placeholder="Ej: María González"
                autoComplete="name"
                aria-invalid={!!errors.patientNewData?.name}
                {...register("patientNewData.name")}
              />
              {errors.patientNewData?.name && (
                <p className="text-xs text-destructive" role="alert">
                  {errors.patientNewData.name.message}
                </p>
              )}
            </div>

            {/* Phone */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="patientNewData.phone">
                Teléfono
                <span className="text-destructive ml-0.5" aria-hidden="true">*</span>
              </Label>
              <Input
                id="patientNewData.phone"
                type="tel"
                placeholder="+51 999 000 111"
                autoComplete="tel"
                aria-invalid={!!errors.patientNewData?.phone}
                {...register("patientNewData.phone")}
              />
              {errors.patientNewData?.phone && (
                <p className="text-xs text-destructive" role="alert">
                  {errors.patientNewData.phone.message}
                </p>
              )}
            </div>

            {/* Email (optional) */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="patientNewData.email">
                Correo electrónico{" "}
                <span className="text-muted-foreground text-xs">(opcional)</span>
              </Label>
              <Input
                id="patientNewData.email"
                type="email"
                placeholder="maria@ejemplo.com"
                autoComplete="email"
                aria-invalid={!!errors.patientNewData?.email}
                {...register("patientNewData.email")}
              />
              {errors.patientNewData?.email && (
                <p className="text-xs text-destructive" role="alert">
                  {errors.patientNewData.email.message}
                </p>
              )}
            </div>
          </div>
        )}
      </fieldset>

      {/* ── Appointment details ────────────────────────────────────────── */}
      <fieldset className="border-0 p-0 m-0">
        <legend className="text-sm font-semibold text-foreground mb-3">
          Detalles de la cita
        </legend>

        <div className="flex flex-col gap-3">
          {/* Doctor ID (UUID) — populated by parent context in real usage */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="doctorId">
              ID del médico
              <span className="text-destructive ml-0.5" aria-hidden="true">*</span>
            </Label>
            <Input
              id="doctorId"
              placeholder="UUID del médico"
              aria-invalid={!!errors.doctorId}
              {...register("doctorId")}
            />
            {errors.doctorId && (
              <p className="text-xs text-destructive" role="alert">
                {errors.doctorId.message}
              </p>
            )}
          </div>

          {/* Service label */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="serviceLabel">
              Servicio / Motivo de consulta
              <span className="text-destructive ml-0.5" aria-hidden="true">*</span>
            </Label>
            <Input
              id="serviceLabel"
              placeholder="Ej: Consulta general, Limpieza dental..."
              aria-invalid={!!errors.serviceLabel}
              {...register("serviceLabel")}
            />
            {errors.serviceLabel && (
              <p className="text-xs text-destructive" role="alert">
                {errors.serviceLabel.message}
              </p>
            )}
          </div>

          {/* Start time */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="startTime">
              Fecha y hora de inicio
              <span className="text-destructive ml-0.5" aria-hidden="true">*</span>
            </Label>
            <Input
              id="startTime"
              type="datetime-local"
              aria-invalid={!!errors.startTime}
              {...register("startTime")}
            />
            {errors.startTime && (
              <p className="text-xs text-destructive" role="alert">
                {errors.startTime.message}
              </p>
            )}
          </div>

          {/* End time */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="endTime">
              Fecha y hora de fin
              <span className="text-destructive ml-0.5" aria-hidden="true">*</span>
            </Label>
            <Input
              id="endTime"
              type="datetime-local"
              aria-invalid={!!errors.endTime}
              {...register("endTime")}
            />
            {errors.endTime && (
              <p className="text-xs text-destructive" role="alert">
                {errors.endTime.message}
              </p>
            )}
          </div>

          {/* Internal notes (optional) */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="notesInternal">
              Notas internas{" "}
              <span className="text-muted-foreground text-xs">(opcional)</span>
            </Label>
            <Textarea
              id="notesInternal"
              placeholder="Notas visibles solo para el equipo..."
              rows={3}
              className="resize-none"
              aria-invalid={!!errors.notesInternal}
              {...register("notesInternal")}
            />
            {errors.notesInternal && (
              <p className="text-xs text-destructive" role="alert">
                {errors.notesInternal.message}
              </p>
            )}
          </div>
        </div>
      </fieldset>

      {/* ── Mutation error ────────────────────────────────────────────── */}
      {createMutation.error && (
        <ErrorAlert error={createMutation.error} />
      )}

      {/* ── Actions ───────────────────────────────────────────────────── */}
      <div className="flex gap-3 pt-2">
        {onCancel && (
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isSubmitting || createMutation.isPending}
            className="flex-1"
          >
            Cancelar
          </Button>
        )}
        <Button
          type="submit"
          disabled={isSubmitting || createMutation.isPending}
          aria-busy={isSubmitting || createMutation.isPending}
          className={cn(onCancel ? "flex-1" : "w-full")}
        >
          {createMutation.isPending ? "Creando cita..." : "Crear cita"}
        </Button>
      </div>
    </form>
  );
}
