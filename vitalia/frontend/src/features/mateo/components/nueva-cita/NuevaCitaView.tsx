// cap: scheduling.mateo-agenda
/**
 * NuevaCitaView.tsx — "Nueva cita" leaf sheet (client root). INTEGRATED.
 * T-FE-4 vitalia-fase2-mateo-nueva-cita
 *
 * FULL-PAGE SHEET (AC-9 — no modal/drawer).
 * Layout: 2-column on lg+. Left = form fields; Right = availability panel.
 * On narrow screens collapses to 1-column stacked.
 *
 * Form sections (left column, MOCKUP ORDER):
 *   1. Canal    → CanalPicker (walk_in | telefono)
 *   2. Paciente → PatientPickerWithCreate (typeahead + inline create)
 *   3. Servicio → ServicePicker → drives default duration + endTime
 *   4+5. Fecha/hora inicio + Duración (2-col row)
 *   6. Hora fin → computed read-only display with "editar" link revealing SmartDateTimePicker
 *   7. Médico   → DoctorPicker
 *   8. Notas internas (optional)
 *
 * Right column:
 *   - AvailabilityChip (doctor + slot selected)
 *   - DayAvailabilityStrip (full strip)
 *   - FreeDoctorsList
 *
 * Validation: RHF + Zod (CreateAppointmentRequestSchema).
 * Submit blocked until form valid AND availabilityStatus === "available" (RN-10).
 * availabilityStatus sourced from Zustand store (set by AvailabilityChip).
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § F3 + 06-tickets.yaml T-FE-4
 */

"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
// useAuth removed — T-FE-4: token no longer resolved here; hooks call getToken() per-request
import { toast } from "sonner";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import {
  EntitySubNavBar,
  SmartDateTimePicker,
  TimePicker,
} from "@luana/ui-kit";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  useNuevaCitaServices,
  useNuevaCitaFreeDoctors,
  useNuevaCitaCreate,
} from "../../hooks/use-nueva-cita";
import type { CreateAppointmentPayload } from "../../hooks/use-nueva-cita";
import { useServiceDayStrips } from "../../hooks/use-availability";
import { useNuevaCitaStore } from "../../store/nueva-cita-store";
import { CreateAppointmentRequestSchema } from "../../types/agenda-schema";
import type { CreateAppointmentRequestDTO } from "../../types/agenda-schema";

// T-FE-2 pickers
import { ServicePicker } from "./ServicePicker";
import { DoctorPicker } from "./DoctorPicker";
import { PatientPickerWithCreate } from "./PatientPickerWithCreate";
import { CanalPicker } from "./CanalPicker";

// T-FE-3 availability
import { AvailabilityChip } from "./AvailabilityChip";
import { DayAvailabilityStrip } from "./DayAvailabilityStrip";
import { FreeDoctorsList } from "./FreeDoctorsList";

// T-FE-4 actions bar
import { NuevaCitaActions } from "./NuevaCitaActions";

// T-D2: tz-correct datetime helpers (extracted for testability · G#1 round-1 tz fix)
import {
  buildIsoFromDateAndTime,
  addMinutesToIso,
  isoToHHMM,
} from "./datetime-utils";

// ── Constants ──────────────────────────────────────────────────────────────────

const DEFAULT_DURATION_MINUTES = 30;

// ── Props ──────────────────────────────────────────────────────────────────────

export interface NuevaCitaViewProps {
  tenantId: string;
  /** Prefilled from URL ?date= (YYYY-MM-DD). PHI-free scheduling data. */
  prefillDate?: string;
  /** Prefilled from URL ?time= (HH:mm). PHI-free scheduling data. */
  prefillTime?: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────────
// buildIsoFromDateAndTime / addMinutesToIso / isoToHHMM moved to ./datetime-utils
// (tz-correct via Intl + unit-tested · G#1 round-1 fix: 08:00 inicio ya no rinde fin 05:30).

// ── Component ──────────────────────────────────────────────────────────────────

/**
 * NuevaCitaView — full-page appointment creation sheet (INTEGRATED T-FE-4).
 *
 * AC-9: This is NOT a modal/drawer — it is a dedicated route page.
 * Back-pill navigates to /mateo/agenda.
 *
 * Submit blocked: !isValid || availabilityStatus !== "available" (RN-10).
 * availabilityStatus sourced from Zustand store (set by AvailabilityChip).
 */
export function NuevaCitaView({
  tenantId,
  prefillDate,
  prefillTime,
}: NuevaCitaViewProps) {
  const router = useRouter();
  // T-FE-4: token state + useEffect REMOVED. Each hook now calls getToken()
  // fresh inside its own queryFn/mutationFn so Clerk can transparently refresh
  // expired JWTs. Cached token caused 307→/sign-in on POST after ~60s.
  const locale = useTenantLocale();
  const timezone = locale.timezone ?? "America/Lima";

  // ── Hora de fin: "editar" toggle (mockup diff #4) ─────────────────────────
  // Default: computed display ("09:30 · ⚙ autocalculado"); "editar" reveals picker
  const [endTimeEditMode, setEndTimeEditMode] = React.useState(false);

  // ── T-D2: Split Fecha / Hora state ───────────────────────────────────────
  // startDateStr: "YYYY-MM-DD" driven by SmartDateTimePicker(showTime=false)
  // startHourStr: "HH:mm"     driven by TimePicker
  // Composed together → setValue("startTime", ...) via handlers below.
  const [startDateStr, setStartDateStr] = React.useState<string>(
    prefillDate ?? "",
  );
  const [startHourStr, setStartHourStr] = React.useState<string>(
    prefillTime ?? "",
  );

  // ── Zustand UI state ──────────────────────────────────────────────────────
  const selectedServiceId = useNuevaCitaStore((s) => s.selectedServiceId);
  const setSelectedServiceId = useNuevaCitaStore((s) => s.setSelectedServiceId);
  const selectedDoctorId = useNuevaCitaStore((s) => s.selectedDoctorId);
  const setSelectedDoctorId = useNuevaCitaStore((s) => s.setSelectedDoctorId);
  const availabilityStatus = useNuevaCitaStore((s) => s.availabilityStatus);
  const patientId = useNuevaCitaStore((s) => s.patientId);
  const setPatientId = useNuevaCitaStore((s) => s.setPatientId);
  const reset = useNuevaCitaStore((s) => s.reset);

  // ── Duration state (driven by selected service, editable by user) ─────────
  const [durationMinutes, setDurationMinutes] = React.useState<number>(
    DEFAULT_DURATION_MINUTES,
  );

  // ── RHF form ──────────────────────────────────────────────────────────────
  const prefillStartIso = React.useMemo(
    () => buildIsoFromDateAndTime(prefillDate, prefillTime, timezone),
    [prefillDate, prefillTime, timezone],
  );

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isValid },
  } = useForm<CreateAppointmentRequestDTO>({
    resolver: zodResolver(CreateAppointmentRequestSchema),
    defaultValues: {
      origin: "walk_in",
      patientId: "",
      doctorId: "",
      serviceLabel: "",
      startTime: prefillStartIso ?? "",
      endTime: prefillStartIso
        ? addMinutesToIso(prefillStartIso, DEFAULT_DURATION_MINUTES)
        : "",
      notesInternal: null,
      currencyOverride: null,
    },
    mode: "onChange",
  });

  const startTime = watch("startTime");
  const endTime = watch("endTime");
  const origin = watch("origin");

  // ── React Query hooks ─────────────────────────────────────────────────────
  const {
    data: servicesData,
    isPending: servicesLoading,
    isError: servicesError,
    refetch: servicesRefetch,
  } = useNuevaCitaServices({ tenantId });

  const {
    data: freeDoctorsData,
    isPending: doctorsLoading,
    isError: doctorsError,
    refetch: doctorsRefetch,
  } = useNuevaCitaFreeDoctors({
    tenantId,
    startIso: startTime,
    durationMinutes,
  });

  const createMutation = useNuevaCitaCreate({ tenantId });

  // T-D3: day-driven multi-doctor strips (service + date → all doctors for the day)
  const {
    data: serviceDayData,
    isPending: serviceDayPending,
    isError: serviceDayError,
  } = useServiceDayStrips({
    tenantId,
    serviceId: selectedServiceId,
    dateLocal: startDateStr,
  });

  // ── Sync selected service → duration default ──────────────────────────────
  React.useEffect(() => {
    if (!selectedServiceId || !servicesData) return;
    const svc = servicesData.items.find((s) => s.offerId === selectedServiceId);
    if (!svc) return;
    const dur = svc.initialApptDurationMinutes ?? DEFAULT_DURATION_MINUTES;
    setDurationMinutes(dur);
    if (startTime) {
      setValue("endTime", addMinutesToIso(startTime, dur), {
        shouldValidate: true,
      });
    }
    setValue("serviceLabel", svc.publicName, { shouldValidate: true });
  }, [selectedServiceId, servicesData, startTime, setValue]);

  // ── Sync selected doctor to form ──────────────────────────────────────────
  // shouldValidate sólo cuando hay un valor REAL: en el mount estos efectos corren
  // con selectedDoctorId/patientId = null → setValue("", {shouldValidate:true})
  // disparaba "ID de médico/paciente inválido" sobre un form PRISTINO (parece roto).
  // Validar sólo en selección real; el form vacío valida recién al submit.
  React.useEffect(() => {
    setValue("doctorId", selectedDoctorId ?? "", { shouldValidate: !!selectedDoctorId });
  }, [selectedDoctorId, setValue]);

  // ── Sync patient to form ──────────────────────────────────────────────────
  React.useEffect(() => {
    setValue("patientId", patientId ?? "", { shouldValidate: !!patientId });
  }, [patientId, setValue]);

  // ── Handlers ──────────────────────────────────────────────────────────────

  // T-D2: Fecha selected → extract date part, compose startTime, cascade endTime
  const handleFechaChange = React.useCallback(
    (iso: string) => {
      const dateStr = iso.slice(0, 10); // "YYYY-MM-DD"
      setStartDateStr(dateStr);
      const composed = buildIsoFromDateAndTime(dateStr, startHourStr, timezone);
      if (composed) {
        setValue("startTime", composed, { shouldValidate: true });
        if (!endTimeEditMode) {
          setValue("endTime", addMinutesToIso(composed, durationMinutes), {
            shouldValidate: true,
          });
        }
      }
    },
    [startHourStr, timezone, endTimeEditMode, durationMinutes, setValue],
  );

  // T-D2: Hora selected → compose startTime, cascade endTime
  const handleHoraChange = React.useCallback(
    (hhmm: string) => {
      setStartHourStr(hhmm);
      const composed = buildIsoFromDateAndTime(startDateStr, hhmm, timezone);
      if (composed) {
        setValue("startTime", composed, { shouldValidate: true });
        if (!endTimeEditMode) {
          setValue("endTime", addMinutesToIso(composed, durationMinutes), {
            shouldValidate: true,
          });
        }
      }
    },
    [startDateStr, timezone, endTimeEditMode, durationMinutes, setValue],
  );

  // obs#1: EntitySubNavBar.rootHref handles back nav deterministically.
  // Cancel still needs to reset store + navigate.
  const handleCancel = React.useCallback(() => {
    reset();
    router.push(`/${tenantId}/mateo/agenda`);
  }, [reset, router, tenantId]);

  const onSubmit = React.useCallback(
    (data: CreateAppointmentRequestDTO) => {
      // offerId (real FK, NOT NULL in BE) comes from the selected service in the
      // store, not from the RHF form (which carries serviceLabel for display).
      const payload = {
        ...data,
        offerId: selectedServiceId ?? "",
      } as CreateAppointmentPayload;
      createMutation.mutate(payload, {
        onSuccess: () => {
          toast.success("Cita creada con éxito");
          reset();
          router.back();
        },
        onError: (err) => {
          const message =
            err instanceof Error
              ? err.message
              : "Error al crear la cita. Intenta de nuevo.";
          toast.error(message);
        },
      });
    },
    [createMutation, reset, router, selectedServiceId],
  );

  // ── Submit block: fail-closed RN-10 ──────────────────────────────────────
  // Block submit when:
  //   - form invalid (required fields missing, fin <= inicio, etc.)
  //   - availability not confirmed AVAILABLE (fail-closed — null = unknown = block)
  const isAvailabilityBlocked =
    availabilityStatus !== "available";

  const submitDisabled = !isValid || isAvailabilityBlocked;

  // H2: compute first blocking reason for hint (only shown when disabled)
  const blockingReason = React.useMemo((): string | null => {
    if (!submitDisabled) return null;
    const w = watch();
    if (!w.patientId) return "Selecciona un paciente para continuar.";
    if (!w.serviceLabel) return "Selecciona un servicio para continuar.";
    if (!w.startTime) return "Selecciona la fecha y hora de inicio.";
    if (!w.doctorId) return "Selecciona un médico para continuar.";
    if (w.endTime && w.startTime && w.endTime <= w.startTime)
      return "La hora de fin debe ser posterior al inicio.";
    if (availabilityStatus === null) return "Verificando disponibilidad del médico…";
    if (availabilityStatus !== "available") return "El médico no está disponible en este horario.";
    return "Completa todos los campos requeridos.";
  }, [submitDisabled, availabilityStatus, watch]);

  // ── Loading gate ──────────────────────────────────────────────────────────
  // ponytail: kept for skeleton; FormPageScaffold removed (obs#1 restructure)
  const isLoading = servicesLoading && !servicesData;

  // ── Computed fin display ──────────────────────────────────────────────────
  const endTimeDisplay = endTime ? isoToHHMM(endTime, timezone) : null;

  return (
    <div className="flex flex-col min-h-0" data-testid="nueva-cita-root">
      {/* obs#1: EntitySubNavBar workspace-mode — full-bleed sticky N3 header */}
      <EntitySubNavBar
        rootHref={`/${tenantId}/mateo/agenda`}
        rootLabel="Agenda"
        entity={{ id: "nueva-cita", name: "Nueva cita" }}
        leaves={[]}
        activeLeaf={null}
      />

      <form
        onSubmit={handleSubmit(onSubmit)}
        noValidate
        data-testid="nueva-cita-form"
        className="flex-1 overflow-auto"
      >
        {/* Loading skeleton */}
        {isLoading ? (
          <div className="p-6">
            <div className="h-4 w-32 animate-pulse rounded bg-muted" />
          </div>
        ) : null}
        <div className="p-6">
          {/* ── 2-col grid: Left = form fields · Right = availability ──────── */}
          {/* obs#2c: fluid responsive — no hardcoded 380px */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[2fr_1fr]">

            {/* ── LEFT COLUMN: Datos de la cita ──────────────────────────────── */}
            {/* obs#2a: wrapped in canonical card */}
            <div
              className="flex flex-col gap-5 rounded-lg border border-border bg-card p-6"
              data-testid="nc-col-form"
            >
              {/* obs#2b: canonical column header — uppercase + muted + tracking + rule */}
              <div>
                <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Datos de la cita
                </h2>
                <hr className="mt-2 border-border" />
              </div>

            {/* ── Sección: Canal ────────────────────────────────────────────── */}
            <section aria-labelledby="nc-canal-label" data-testid="nc-section-canal">
              <Label
                id="nc-canal-label"
                className="mb-1.5 block text-sm font-medium"
              >
                Canal de ingreso
              </Label>
              <Controller
                name="origin"
                control={control}
                render={({ field }) => (
                  <CanalPicker
                    value={field.value as "walk_in" | "telefono"}
                    onChange={(canal) => field.onChange(canal)}
                  />
                )}
              />
              {errors.origin ? (
                <p className="mt-1 text-xs text-destructive" role="alert">
                  {errors.origin.message}
                </p>
              ) : null}
            </section>

            {/* ── Sección: Paciente ─────────────────────────────────────────── */}
            <section aria-labelledby="nc-paciente-label" data-testid="nc-section-paciente">
              <Label
                id="nc-paciente-label"
                className="mb-1.5 block text-sm font-medium"
              >
                Paciente
              </Label>
              <PatientPickerWithCreate
                value={patientId}
                tenantId={tenantId}
                uiChannel={origin === "walk_in" ? "walk_in" : "telefono"}
                onChange={(resolvedPatientId) => {
                  setPatientId(resolvedPatientId);
                  setValue("patientId", resolvedPatientId, { shouldValidate: true });
                }}
              />
              {errors.patientId ? (
                <p className="mt-1 text-xs text-destructive" role="alert">
                  {errors.patientId.message}
                </p>
              ) : null}
            </section>

            {/* ── Sección: Servicio ─────────────────────────────────────────── */}
            <section aria-labelledby="nc-servicio-label" data-testid="nc-section-servicio">
              <Label
                id="nc-servicio-label"
                className="mb-1.5 block text-sm font-medium"
              >
                Servicio
              </Label>
              <ServicePicker
                services={servicesData?.items ?? []}
                value={selectedServiceId}
                loading={servicesLoading}
                error={servicesError}
                onRetry={() => void servicesRefetch()}
                onChange={({ offerId, durationMinutes: dur }) => {
                  setSelectedServiceId(offerId);
                  if (dur != null) {
                    setDurationMinutes(dur);
                    if (startTime) {
                      setValue("endTime", addMinutesToIso(startTime, dur), {
                        shouldValidate: true,
                      });
                    }
                  }
                }}
              />
              {errors.serviceLabel ? (
                <p className="mt-1 text-xs text-destructive" role="alert">
                  {errors.serviceLabel.message}
                </p>
              ) : null}
            </section>

            {/* ── Secciones: Fecha inicio + Hora inicio + Duración (3-col · T-D2) ── */}
            <div className="grid grid-cols-3 gap-4" data-testid="nc-row-2">
              {/* Fecha de inicio (date-only picker · T-D2) */}
              <section aria-labelledby="nc-fecha-label" data-testid="nc-section-fecha">
                <Label
                  id="nc-fecha-label"
                  className="mb-1.5 block text-sm font-medium"
                >
                  Fecha
                </Label>
                <SmartDateTimePicker
                  showTime={false}
                  disablePast
                  value={startDateStr ? (buildIsoFromDateAndTime(startDateStr, "12:00", timezone) ?? "") : ""}
                  onChange={handleFechaChange}
                  timezone={timezone}
                  placeholder="DD/MM/AAAA"
                />
              </section>

              {/* Hora de inicio (time-only picker · T-D2) */}
              <section aria-labelledby="nc-hora-label" data-testid="nc-section-hora">
                <Label
                  id="nc-hora-label"
                  className="mb-1.5 block text-sm font-medium"
                >
                  Hora de inicio
                </Label>
                <TimePicker
                  value={startHourStr}
                  onChange={handleHoraChange}
                  aria-label="Hora de inicio"
                />
                {errors.startTime ? (
                  <p className="mt-1 text-xs text-destructive" role="alert">
                    {errors.startTime.message}
                  </p>
                ) : null}
              </section>

              {/* Duración */}
              <section aria-labelledby="nc-duracion-label" data-testid="nc-section-duracion">
                <Label
                  id="nc-duracion-label"
                  htmlFor="nc-duracion"
                  className="mb-1.5 block text-sm font-medium"
                >
                  Duración (min)
                </Label>
                <Input
                  id="nc-duracion"
                  type="number"
                  min={1}
                  max={480}
                  value={durationMinutes}
                  data-testid="nc-duracion-input"
                  onChange={(e) => {
                    const dur = Math.max(
                      1,
                      parseInt(e.target.value, 10) || DEFAULT_DURATION_MINUTES,
                    );
                    setDurationMinutes(dur);
                    // L2: only overwrite endTime when user hasn't manually set it
                    if (startTime && !endTimeEditMode) {
                      setValue("endTime", addMinutesToIso(startTime, dur), {
                        shouldValidate: true,
                      });
                    }
                  }}
                />
                {/* M3: helper text — duration origin */}
                <p className="mt-1 text-xs text-muted-foreground" data-testid="nc-duracion-hint">
                  Viene del servicio · editable
                </p>
              </section>
            </div>

            {/* ── Sección: Hora de fin ──────────────────────────────────────── */}
            <section aria-labelledby="nc-fin-label" data-testid="nc-section-fin">
              <Label
                id="nc-fin-label"
                className="mb-1.5 block text-sm font-medium"
              >
                Hora de fin
              </Label>
              {endTimeEditMode ? (
                /* Manual edit mode — full SmartDateTimePicker */
                <div className="flex flex-col gap-1">
                  <Controller
                    name="endTime"
                    control={control}
                    render={({ field }) => (
                      <SmartDateTimePicker
                        value={field.value}
                        onChange={field.onChange}
                        timezone={timezone}
                        placeholder="Fin del turno..."
                      />
                    )}
                  />
                  <button
                    type="button"
                    className="self-start text-xs text-muted-foreground underline hover:text-foreground"
                    onClick={() => setEndTimeEditMode(false)}
                  >
                    volver a autocalculado
                  </button>
                </div>
              ) : (
                /* Computed display (default) */
                <div className="flex items-center gap-2 rounded-md border border-input bg-muted/50 px-3 py-2 text-sm">
                  {endTimeDisplay ? (
                    <>
                      <span className="font-medium tabular-nums">{endTimeDisplay}</span>
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <svg
                          aria-hidden="true"
                          className="h-3 w-3"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M10.343 3.94c.09-.542.56-.94 1.11-.94h1.093c.55 0 1.02.398 1.11.94l.149.894c.07.424.384.764.78.93.398.164.855.142 1.205-.108l.737-.527a1.125 1.125 0 0 1 1.45.12l.773.774c.39.389.44 1.002.12 1.45l-.527.737c-.25.35-.272.806-.107 1.204.165.397.505.71.93.78l.893.15c.543.09.94.559.94 1.109v1.094c0 .55-.397 1.02-.94 1.11l-.894.149c-.424.07-.764.383-.929.78-.165.398-.143.854.107 1.204l.527.738c.32.447.269 1.06-.12 1.45l-.774.773a1.125 1.125 0 0 1-1.449.12l-.738-.527c-.35-.25-.806-.272-1.203-.107-.398.165-.71.505-.781.929l-.149.894c-.09.542-.56.94-1.11.94h-1.094c-.55 0-1.019-.398-1.11-.94l-.148-.894c-.071-.424-.384-.764-.781-.93-.398-.164-.854-.142-1.204.108l-.738.527c-.447.32-1.06.269-1.45-.12l-.773-.774a1.125 1.125 0 0 1-.12-1.45l.527-.737c.25-.35.272-.806.108-1.204-.165-.397-.506-.71-.93-.78l-.894-.15c-.542-.09-.94-.56-.94-1.109v-1.094c0-.55.398-1.02.94-1.11l.894-.149c.424-.07.764-.384.93-.781.165-.397.143-.854-.108-1.204l-.526-.738a1.125 1.125 0 0 1 .12-1.45l.773-.773a1.125 1.125 0 0 1 1.45-.12l.737.527c.35.25.807.272 1.204.107.397-.165.71-.505.78-.929l.15-.894Z"
                          />
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                        </svg>
                        autocalculado
                      </span>
                      <button
                        type="button"
                        className="ml-auto text-xs text-primary underline hover:opacity-80"
                        onClick={() => setEndTimeEditMode(true)}
                        data-testid="nc-fin-editar"
                      >
                        editar
                      </button>
                    </>
                  ) : (
                    <span className="text-muted-foreground">
                      Se calculará al seleccionar inicio y duración
                    </span>
                  )}
                </div>
              )}
              {/* fin ≤ inicio error (SC-fin-invalido) */}
              {errors.endTime ? (
                <p
                  className="mt-1 text-xs text-destructive"
                  role="alert"
                  data-testid="nc-end-time-error"
                >
                  {errors.endTime.message}
                </p>
              ) : null}
            </section>

            {/* ── Sección: Médico ───────────────────────────────────────────── */}
            <section aria-labelledby="nc-medico-label" data-testid="nc-section-medico">
              <Label
                id="nc-medico-label"
                className="mb-1.5 block text-sm font-medium"
              >
                Médico
              </Label>
              <DoctorPicker
                doctors={freeDoctorsData?.doctors ?? []}
                value={selectedDoctorId}
                loading={doctorsLoading && !!startTime}
                disabled={!startTime}
                disabledReason="Selecciona fecha y hora primero"
                error={doctorsError}
                onRetry={() => void doctorsRefetch()}
                onChange={(doctorId) => setSelectedDoctorId(doctorId)}
              />
              {/* M5: inline chip below DoctorPicker on mobile (hidden on lg+ where rail shows) */}
              {selectedDoctorId && startTime ? (
                <div className="mt-2 lg:hidden" data-testid="nc-availability-chip-inline">
                  <AvailabilityChip
                    tenantId={tenantId}
                    doctorId={selectedDoctorId}
                    startIso={startTime}
                    durationMinutes={durationMinutes}
                  />
                </div>
              ) : null}
              {errors.doctorId ? (
                <p className="mt-1 text-xs text-destructive" role="alert">
                  {errors.doctorId.message}
                </p>
              ) : null}
            </section>

            {/* ── Sección: Notas internas (opcional) ───────────────────────── */}
            <section aria-labelledby="nc-notas-label" data-testid="nc-section-notas">
              <Label
                id="nc-notas-label"
                htmlFor="nc-notas"
                className="mb-1.5 block text-sm font-medium"
              >
                Notas internas{" "}
                <span className="text-xs font-normal text-muted-foreground">
                  (opcional)
                </span>
              </Label>
              <Controller
                name="notesInternal"
                control={control}
                render={({ field }) => (
                  <>
                    <Textarea
                      id="nc-notas"
                      placeholder="Solo logística — sin información clínica. Ej: la paciente prefiere las mañanas."
                      maxLength={500}
                      data-testid="nc-notas-textarea"
                      value={field.value ?? ""}
                      onChange={(e) => field.onChange(e.target.value || null)}
                      className="resize-none"
                      rows={3}
                    />
                    {/* L6: character counter */}
                    <p
                      className="mt-1 text-right text-xs text-muted-foreground"
                      aria-live="polite"
                      data-testid="nc-notas-counter"
                    >
                      {(field.value ?? "").length}/500
                    </p>
                  </>
                )}
              />
            </section>
            </div>{/* end left card */}

            {/* ── RIGHT COLUMN: Disponibilidad del médico ────────────────────── */}
            {/* obs#2a: wrapped in canonical card */}
            <div
              className="flex flex-col gap-4 rounded-lg border border-border bg-card p-6"
              data-testid="nc-col-avail"
            >
              {/* obs#2b: canonical column header — uppercase + muted + tracking + rule */}
              <div>
                <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Disponibilidad del médico
                </h2>
                <hr className="mt-2 border-border" />
              </div>

            {/* M1: intro block — shown when no date selected yet */}
            {!startDateStr ? (
              <div
                data-testid="nc-avail-intro"
                className="rounded-md border border-dashed border-border bg-muted/30 p-4 text-sm text-muted-foreground"
              >
                <p className="font-medium text-foreground">¿Qué verás aquí?</p>
                <ul className="mt-2 list-disc space-y-1 pl-4">
                  <li>Disponibilidad del médico en el horario elegido</li>
                  <li>Vista del día con bloques libres y ocupados</li>
                  <li>Médicos disponibles en ese horario</li>
                </ul>
                <p className="mt-3 text-xs">Selecciona la fecha y hora de inicio para comenzar.</p>
              </div>
            ) : null}

            {/* AvailabilityChip: shows when doctor + slot selected (T-FE-3) */}
            {selectedDoctorId && startTime ? (
              <div data-testid="nc-availability-chip-container">
                <AvailabilityChip
                  tenantId={tenantId}
                  doctorId={selectedDoctorId}
                  startIso={startTime}
                  durationMinutes={durationMinutes}
                />
              </div>
            ) : null}

            {/* DayAvailabilityStrip: N-doctor swimlanes (T-D3 day-driven) */}
            {selectedServiceId && startDateStr ? (
              <div data-testid="nc-day-strip-container">
                <DayAvailabilityStrip
                  doctors={serviceDayData?.doctors ?? []}
                  isPending={serviceDayPending}
                  isError={serviceDayError}
                  dateLocal={startDateStr}
                  selectedStartIso={startTime || null}
                  selectedEndIso={endTime || null}
                  selectedDoctorId={selectedDoctorId}
                  onSelectDoctor={(doctorId) => setSelectedDoctorId(doctorId)}
                  timezone={timezone}
                />
              </div>
            ) : null}

            {/* FreeDoctorsList: time-filtered 1-click select (T-D3 re-role) */}
            <div data-testid="nc-free-doctors-container">
              <FreeDoctorsList
                tenantId={tenantId}
                doctors={serviceDayData?.doctors ?? []}
                startHourStr={startHourStr}
                timezone={timezone}
              />
            </div>
            </div>{/* end right card */}
          </div>{/* end 2-col grid */}
        </div>{/* end p-6 */}

        {/* ── NuevaCitaActions — sticky bottom (T-FE-4) ─────────────────────── */}
        {/* H2: show blocking reason as role="status" when submit is disabled */}
        {submitDisabled && blockingReason ? (
          <p
            role="status"
            aria-live="polite"
            data-testid="nc-blocking-reason"
            className="px-4 pb-1 text-center text-xs text-muted-foreground"
          >
            {blockingReason}
          </p>
        ) : null}
        <NuevaCitaActions
          onCancel={handleCancel}
          onSubmit={handleSubmit(onSubmit)}
          submitting={createMutation.isPending}
          submitDisabled={submitDisabled}
          hint={
            // M4: hidden on mobile (≤sm) to avoid clash with Valeria FAB
            <span className="hidden sm:inline">
              Sin guardar todavía · los datos no se pierden si navegas dentro de la hoja.
            </span>
          }
        />
      </form>
    </div>
  );
}
