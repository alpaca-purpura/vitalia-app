// cap: scheduling.mateo-agenda
/**
 * use-nueva-cita.ts — React Query hooks for the "Nueva cita" leaf sheet.
 * T-FE-1 vitalia-fase2-mateo-nueva-cita
 *
 * Key convention: ["mateo","nueva-cita",action,...stableFilters]
 *
 * BE returns snake_case — this layer normalizes to camelCase before returning
 * to the component. (Pattern: same approach as normalize-agenda.ts, but inline
 * since these are new endpoints for this story only.)
 *
 * HIPAA-lite:
 *   - PHI (patient data) never in URL params.
 *   - X-Clinic-ID + X-User-ID + X-User-Role headers required (dual filter).
 *   - fetchClient (vitaliaFetch) auto-injects X-Tenant-ID.
 *
 * ★ ANTI-EMBUDO CONTRACT (verified against BE DTOs 2026-06-22):
 *   - Services: GET /api/v1/offer/servicios → ServiceListResponse (snake_case)
 *     Fields: offer_id, public_name, initial_appt_duration_minutes, is_active, status, currency
 *   - FreeDoctors: POST /api/v1/scheduling/availability/free-doctors → FreeDoctorsResponse
 *     Fields: doctors[{doctor_id, doctor_label}], count
 *   - AvailabilityCheck: POST /api/v1/scheduling/availability/check → AvailabilityCheckResponse
 *     Fields: status, conflict_label, conflict_start
 *   - CreateAppointment: POST /api/v1/scheduling/appointments
 *     Request snake_case: origin, patient_id, doctor_id, service_label, start_time, end_time
 *     Response: appointment_id, patient_id, doctor_id, start_time, end_time (snake_case)
 *   - PatientSearch: GET /api/v1/crm/patients?q= → PatientSearchResponse
 *     Fields: items[{patient_id, name_masked, phone_masked, channel_first, created_at}]
 *   - PatientInlineCreate: POST /api/v1/crm/patients
 *     Request: name, phone, email, channel (channel is "walk_in"|"phone"|etc — NOT "telefono")
 *     Response: patient_id, name_masked, phone_masked, is_duplicate, created_at
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE hooks; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § F3 + 06-tickets.yaml T-FE-1
 */

"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { vitaliaFetch } from "@/lib/fetch-client";
import { useActorHeaders } from "@/hooks/useActorHeaders";
import { useClinicId } from "@/hooks/useClinicId";

// ────────────────────────────────────────────────────────────────────────────
// Shared query key factory
// ────────────────────────────────────────────────────────────────────────────

export const nuevaCitaKeys = {
  services: (tenantId: string) =>
    ["mateo", "nueva-cita", "services", tenantId] as const,
  freeDoctors: (
    tenantId: string,
    startIso: string,
    durationMinutes: number,
  ) =>
    [
      "mateo",
      "nueva-cita",
      "free-doctors",
      tenantId,
      startIso,
      durationMinutes,
    ] as const,
  availabilityCheck: (
    tenantId: string,
    doctorId: string,
    startIso: string,
    durationMinutes: number,
  ) =>
    [
      "mateo",
      "nueva-cita",
      "availability",
      tenantId,
      doctorId,
      startIso,
      durationMinutes,
    ] as const,
  patientSearch: (tenantId: string, q: string) =>
    ["mateo", "nueva-cita", "patient-search", tenantId, q] as const,
};

// ────────────────────────────────────────────────────────────────────────────
// Normalized response types (camelCase FE DTOs)
// ────────────────────────────────────────────────────────────────────────────

export interface NuevaCitaServiceItem {
  offerId: string;
  publicName: string;
  modality: string;
  isActive: boolean;
  status: string;
  initialApptDurationMinutes: number | null;
  price: string | null;
  currency: string | null;
  category: string | null;
}

export interface NuevaCitaServicesResponse {
  items: NuevaCitaServiceItem[];
  nextCursor: string | null;
}

export interface NuevaCitaDoctorItem {
  doctorId: string;
  doctorLabel: string;
}

export interface NuevaCitaFreeDoctorsResponse {
  doctors: NuevaCitaDoctorItem[];
  count: number;
}

export type AvailabilityStatus =
  | "available"
  | "busy"
  | "out_of_hours"
  | "no_schedule";

export interface NuevaCitaAvailabilityResponse {
  status: AvailabilityStatus;
  conflictLabel: string | null;
  conflictStart: string | null;
}

export interface NuevaCitaCreatedAppointment {
  appointmentId: string;
  patientId: string;
  doctorId: string;
  startTime: string;
  endTime: string;
}

export interface NuevaCitaPatientSearchItem {
  patientId: string;
  nameMasked: string;
  phoneMasked: string | null;
  channelFirst: string | null;
}

export interface NuevaCitaPatientSearchResponse {
  items: NuevaCitaPatientSearchItem[];
  nextCursor: string | null;
  totalApprox: number;
}

export interface NuevaCitaPatientInlineCreateResponse {
  patientId: string;
  nameMasked: string;
  phoneMasked: string | null;
  isDuplicate: boolean;
}

// ────────────────────────────────────────────────────────────────────────────
// FE → BE request types (camelCase in FE, serialized to snake_case for BE)
// ────────────────────────────────────────────────────────────────────────────

export interface CreateAppointmentPayload {
  origin: "walk_in" | "telefono";
  patientId: string;
  /** offerId (UUID) of the selected service — real FK, required by BE (NOT NULL). */
  offerId: string;
  doctorId: string;
  serviceLabel: string;
  startTime: string;
  endTime: string;
  notesInternal: string | null;
  currencyOverride: string | null;
}

/** Channel for patient inline create — BE literal. "walk_in"|"phone"|"other" etc. */
type PatientChannel =
  | "whatsapp"
  | "instagram"
  | "web"
  | "phone"
  | "walk_in"
  | "other";

export interface PatientInlineCreatePayload {
  name: string;
  phone: string | null;
  email: string | null;
  /** Maps from Mateo origin: "walk_in"→"walk_in", "telefono"→"phone" */
  channel: PatientChannel;
  note: string | null;
}

// ────────────────────────────────────────────────────────────────────────────
// Normalizers (snake_case BE → camelCase FE)
// ────────────────────────────────────────────────────────────────────────────

type Raw = Record<string, unknown>;

function normalizeService(raw: Raw): NuevaCitaServiceItem {
  return {
    offerId: String(raw.offer_id ?? ""),
    publicName: String(raw.public_name ?? ""),
    modality: String(raw.modality ?? ""),
    isActive: Boolean(raw.is_active),
    status: String(raw.status ?? ""),
    initialApptDurationMinutes:
      typeof raw.initial_appt_duration_minutes === "number"
        ? raw.initial_appt_duration_minutes
        : null,
    price: raw.price != null ? String(raw.price) : null,
    currency: raw.currency != null ? String(raw.currency) : null,
    category: raw.category != null ? String(raw.category) : null,
  };
}

function normalizeDoctor(raw: Raw): NuevaCitaDoctorItem {
  return {
    doctorId: String(raw.doctor_id ?? ""),
    doctorLabel: String(raw.doctor_label ?? ""),
  };
}

function normalizeAvailability(raw: Raw): NuevaCitaAvailabilityResponse {
  return {
    status: (raw.status as AvailabilityStatus) ?? "no_schedule",
    conflictLabel: raw.conflict_label != null ? String(raw.conflict_label) : null,
    conflictStart: raw.conflict_start != null ? String(raw.conflict_start) : null,
  };
}

function normalizeCreatedAppointment(raw: Raw): NuevaCitaCreatedAppointment {
  return {
    appointmentId: String(raw.appointment_id ?? ""),
    patientId: String(raw.patient_id ?? ""),
    doctorId: String(raw.doctor_id ?? ""),
    startTime: String(raw.start_time ?? ""),
    endTime: String(raw.end_time ?? ""),
  };
}

function normalizePatientSearchItem(raw: Raw): NuevaCitaPatientSearchItem {
  return {
    patientId: String(raw.patient_id ?? ""),
    nameMasked: String(raw.name_masked ?? ""),
    phoneMasked: raw.phone_masked != null ? String(raw.phone_masked) : null,
    channelFirst: raw.channel_first != null ? String(raw.channel_first) : null,
  };
}

// ────────────────────────────────────────────────────────────────────────────
// Serializers (camelCase FE → snake_case BE for request bodies)
// ────────────────────────────────────────────────────────────────────────────

function serializeCreateAppointment(
  payload: CreateAppointmentPayload,
): Record<string, unknown> {
  return {
    origin: payload.origin,
    patient_id: payload.patientId,
    offer_id: payload.offerId,
    doctor_id: payload.doctorId,
    service_label: payload.serviceLabel,
    start_time: payload.startTime,
    end_time: payload.endTime,
    notes_internal: payload.notesInternal,
    currency_override: payload.currencyOverride,
  };
}

// ────────────────────────────────────────────────────────────────────────────
// Hook params
// token removed — hooks call getToken() fresh inside queryFn/mutationFn
// to avoid stale-token bug (Clerk JWTs expire ~60s; caching at mount breaks
// POST requests after long form fills). T-FE-4.
// ────────────────────────────────────────────────────────────────────────────

interface BaseParams {
  tenantId: string;
}

// ────────────────────────────────────────────────────────────────────────────
// useNuevaCitaServices — GET /api/v1/offer/servicios
// ────────────────────────────────────────────────────────────────────────────

/**
 * Load active service list for the nueva-cita form.
 * Prefills initialApptDurationMinutes → default end time.
 */
export function useNuevaCitaServices({ tenantId }: BaseParams) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const actorHeaders = useActorHeaders();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: nuevaCitaKeys.services(tenantId),
    queryFn: async (): Promise<NuevaCitaServicesResponse> => {
      const token = await getToken();
      const raw = await vitaliaFetch<{
        items: Raw[];
        next_cursor: string | null;
      }>("/api/v1/offer/servicios?is_active=true&limit=100", {
        token: token ?? "",
        tenantId,
        headers: {
          ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
          ...actorHeaders,
        },
      });
      return {
        items: raw.items.map(normalizeService),
        nextCursor: raw.next_cursor ?? null,
      };
    },
    enabled: isLoaded && Boolean(isSignedIn) && Boolean(tenantId),
    staleTime: 60_000, // services change infrequently
  });
}

// ────────────────────────────────────────────────────────────────────────────
// useNuevaCitaFreeDoctors — POST /api/v1/scheduling/availability/free-doctors
// ────────────────────────────────────────────────────────────────────────────

interface FreeDoctorsParams extends BaseParams {
  startIso: string;
  durationMinutes: number;
}

/**
 * List doctors free at the given slot.
 * Disabled until startIso is non-empty.
 */
export function useNuevaCitaFreeDoctors({
  tenantId,
  startIso,
  durationMinutes,
}: FreeDoctorsParams) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const actorHeaders = useActorHeaders();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: nuevaCitaKeys.freeDoctors(tenantId, startIso, durationMinutes),
    queryFn: async (): Promise<NuevaCitaFreeDoctorsResponse> => {
      const token = await getToken();
      const raw = await vitaliaFetch<{
        doctors: Raw[];
        count: number;
      }>("/api/v1/scheduling/availability/free-doctors", {
        method: "POST",
        token: token ?? "",
        tenantId,
        headers: {
          ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
          ...actorHeaders,
        },
        body: JSON.stringify({
          start: startIso,
          duration_minutes: durationMinutes,
        }),
      });
      return {
        doctors: raw.doctors.map(normalizeDoctor),
        count: raw.count,
      };
    },
    enabled: isLoaded && Boolean(isSignedIn) && Boolean(tenantId) && Boolean(startIso),
    staleTime: 30_000,
  });
}

// ────────────────────────────────────────────────────────────────────────────
// useNuevaCitaAvailabilityCheck — POST /api/v1/scheduling/availability/check
// ────────────────────────────────────────────────────────────────────────────

interface AvailabilityCheckParams extends BaseParams {
  doctorId: string | null;
  startIso: string;
  durationMinutes: number;
}

/**
 * Check 4-state availability for a specific doctor + slot.
 * Disabled until doctorId is selected.
 */
export function useNuevaCitaAvailabilityCheck({
  tenantId,
  doctorId,
  startIso,
  durationMinutes,
}: AvailabilityCheckParams) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const actorHeaders = useActorHeaders();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: nuevaCitaKeys.availabilityCheck(
      tenantId,
      doctorId ?? "",
      startIso,
      durationMinutes,
    ),
    queryFn: async (): Promise<NuevaCitaAvailabilityResponse> => {
      const token = await getToken();
      const raw = await vitaliaFetch<Raw>(
        "/api/v1/scheduling/availability/check",
        {
          method: "POST",
          token: token ?? "",
          tenantId,
          headers: {
            ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
            ...actorHeaders,
          },
          body: JSON.stringify({
            doctor_id: doctorId,
            start: startIso,
            duration_minutes: durationMinutes,
          }),
        },
      );
      return normalizeAvailability(raw);
    },
    enabled:
      isLoaded &&
      Boolean(isSignedIn) &&
      Boolean(tenantId) &&
      Boolean(doctorId) &&
      Boolean(startIso),
    staleTime: 15_000,
  });
}

// ────────────────────────────────────────────────────────────────────────────
// useNuevaCitaCreate — POST /api/v1/scheduling/appointments
// ────────────────────────────────────────────────────────────────────────────

/**
 * Create a new appointment.
 * Invalidates agenda grid on success so the calendar refreshes.
 */
export function useNuevaCitaCreate({ tenantId }: BaseParams) {
  const { getToken } = useAuth();
  const qc = useQueryClient();
  const actorHeaders = useActorHeaders();
  const clinicId = useClinicId();

  return useMutation({
    mutationFn: async (
      payload: CreateAppointmentPayload,
    ): Promise<NuevaCitaCreatedAppointment> => {
      const token = await getToken();
      const raw = await vitaliaFetch<Raw>(
        "/api/v1/scheduling/appointments",
        {
          method: "POST",
          token: token ?? "",
          tenantId,
          headers: {
            ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
            ...actorHeaders,
          },
          body: JSON.stringify(serializeCreateAppointment(payload)),
        },
      );
      return normalizeCreatedAppointment(raw);
    },
    onSuccess: () => {
      // Invalidate agenda grid so the new appointment shows up
      void qc.invalidateQueries({ queryKey: ["mateo", "agenda"] });
    },
  });
}

// ────────────────────────────────────────────────────────────────────────────
// useNuevaCitaPatientSearch — GET /api/v1/crm/patients?q=
// ────────────────────────────────────────────────────────────────────────────

interface PatientSearchParams extends BaseParams {
  q: string;
}

/**
 * Typeahead patient search — debounce on the consumer side.
 * Disabled until q is at least 2 chars (avoid full-table scan).
 */
export function useNuevaCitaPatientSearch({
  tenantId,
  q,
}: PatientSearchParams) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const actorHeaders = useActorHeaders();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: nuevaCitaKeys.patientSearch(tenantId, q),
    queryFn: async (): Promise<NuevaCitaPatientSearchResponse> => {
      const token = await getToken();
      const url = `/api/v1/crm/patients?q=${encodeURIComponent(q)}&limit=20`;
      const raw = await vitaliaFetch<{
        items: Raw[];
        next_cursor: string | null;
        total_approx: number;
      }>(url, {
        token: token ?? "",
        tenantId,
        headers: {
          ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
          ...actorHeaders,
        },
      });
      return {
        items: raw.items.map(normalizePatientSearchItem),
        nextCursor: raw.next_cursor ?? null,
        totalApprox: raw.total_approx ?? 0,
      };
    },
    enabled: isLoaded && Boolean(isSignedIn) && Boolean(tenantId) && q.length >= 2,
    staleTime: 30_000,
  });
}

// ────────────────────────────────────────────────────────────────────────────
// useNuevaCitaPatientInlineCreate — POST /api/v1/crm/patients
// ────────────────────────────────────────────────────────────────────────────

/**
 * Inline patient create for walk-in / phone origin.
 * Returns masked fields only (HIPAA-lite).
 */
export function useNuevaCitaPatientInlineCreate({
  tenantId,
}: BaseParams) {
  const { getToken } = useAuth();
  const actorHeaders = useActorHeaders();
  const clinicId = useClinicId();

  return useMutation({
    mutationFn: async (
      payload: PatientInlineCreatePayload,
    ): Promise<NuevaCitaPatientInlineCreateResponse> => {
      const token = await getToken();
      const raw = await vitaliaFetch<Raw>("/api/v1/crm/patients", {
        method: "POST",
        token: token ?? "",
        tenantId,
        headers: {
          ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
          ...actorHeaders,
        },
        body: JSON.stringify({
          name: payload.name,
          phone: payload.phone,
          email: payload.email,
          channel: payload.channel,
          note: payload.note,
        }),
      });
      return {
        patientId: String(raw.patient_id ?? ""),
        nameMasked: String(raw.name_masked ?? ""),
        phoneMasked: raw.phone_masked != null ? String(raw.phone_masked) : null,
        isDuplicate: Boolean(raw.is_duplicate),
      };
    },
  });
}
