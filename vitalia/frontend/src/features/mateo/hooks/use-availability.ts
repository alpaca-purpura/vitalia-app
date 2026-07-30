// cap: scheduling.mateo-agenda
/**
 * use-availability.ts — React Query hooks for T-FE-3 availability surface.
 * T-FE-3 vitalia-fase2-mateo-nueva-cita
 *
 * DEBOUNCED useAvailabilityCheck (400ms) — revalidates on slot/service/doctor change.
 * useDayStrip — day-view time blocks (SC-mini-vista AC-8).
 *
 * Key convention: ["mateo","availability",action,...stableFilters]
 * Mirrors nuevaCitaKeys factory but scoped to availability endpoints only.
 *
 * ANTI-EMBUDO — field names verified against T-BE-3 DTOs:
 *   AvailabilityCheckResponse: status, conflict_label, conflict_start
 *   DayStripResponse:          doctor_id, date, blocks[{kind, start, end}]
 *   (use-nueva-cita.ts owns free-doctors + availability-check base hooks)
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE hooks; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § F3 + 06-tickets.yaml T-FE-3
 */

"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { vitaliaFetch } from "@/lib/fetch-client";
import { useActorHeaders } from "@/hooks/useActorHeaders";
import { useClinicId } from "@/hooks/useClinicId";
import type { AvailabilityStatus, NuevaCitaAvailabilityResponse } from "./use-nueva-cita";
import type { ServiceDayResponse } from "../types/agenda-schema";

// ── Types ──────────────────────────────────────────────────────────────────

export interface DayStripBlock {
  kind: "working_hours" | "busy" | "unavailable";
  start: string; // ISO 8601 UTC
  end: string;   // ISO 8601 UTC
}

export interface DayStripData {
  doctorId: string;
  dateLocal: string;
  blocks: DayStripBlock[];
}

// ── Query key factory ──────────────────────────────────────────────────────

export const availabilityKeys = {
  check: (
    tenantId: string,
    doctorId: string,
    startIso: string,
    durationMinutes: number,
  ) =>
    [
      "mateo",
      "availability",
      "check",
      tenantId,
      doctorId,
      startIso,
      durationMinutes,
    ] as const,

  dayStrip: (tenantId: string, doctorId: string, dateLocal: string) =>
    ["mateo", "availability", "day-strip", tenantId, doctorId, dateLocal] as const,

  /** T-D3: includes dateLocal → React Query auto-refetches on day change. */
  serviceDay: (tenantId: string, serviceId: string, dateLocal: string) =>
    ["mateo", "availability", "service-day", tenantId, serviceId, dateLocal] as const,
};

// ── Raw normalizers ────────────────────────────────────────────────────────

type Raw = Record<string, unknown>;

function normalizeAvailability(raw: Raw): NuevaCitaAvailabilityResponse {
  return {
    status: (raw.status as AvailabilityStatus) ?? "no_schedule",
    conflictLabel: raw.conflict_label != null ? String(raw.conflict_label) : null,
    conflictStart: raw.conflict_start != null ? String(raw.conflict_start) : null,
  };
}

function normalizeDayStrip(raw: Raw): DayStripData {
  const blocks = Array.isArray(raw.blocks)
    ? (raw.blocks as Raw[]).map((b) => ({
        kind: (b.kind as DayStripBlock["kind"]) ?? "unavailable",
        start: String(b.start ?? ""),
        end: String(b.end ?? ""),
      }))
    : [];
  return {
    doctorId: String(raw.doctor_id ?? ""),
    dateLocal: String(raw.date ?? ""),
    blocks,
  };
}

// ── useAvailabilityCheck (DEBOUNCED 400ms) ─────────────────────────────────

interface AvailabilityCheckParams {
  tenantId: string;
  // token removed — getToken() called fresh inside queryFn (T-FE-4 fix)
  doctorId: string | null;
  startIso: string;
  durationMinutes: number;
}

/**
 * Debounced availability check (400ms).
 * Disabled until doctorId is set + startIso is non-empty.
 * Exposes `isAvailable` derived boolean for T-FE-4 submit block.
 *
 * SC-disponibilidad-falla: endpoint down → isError=true; chip shows retry.
 * SC-revalida-cambio: key changes when slot/duration/doctor changes → React Query refetches.
 */
export function useAvailabilityCheck({
  tenantId,
  doctorId,
  startIso,
  durationMinutes,
}: AvailabilityCheckParams) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const actorHeaders = useActorHeaders();
  const clinicId = useClinicId();

  // Debounce the query key — don't fire on every keystroke
  const [debouncedKey, setDebouncedKey] = React.useState<
    readonly [string, string, string, string, string, string, number] | null
  >(null);

  React.useEffect(() => {
    if (!doctorId || !startIso) {
      setDebouncedKey(null);
      return;
    }
    const id = setTimeout(() => {
      setDebouncedKey(
        availabilityKeys.check(tenantId, doctorId, startIso, durationMinutes),
      );
    }, 400);
    return () => clearTimeout(id);
  }, [tenantId, doctorId, startIso, durationMinutes]);

  const query = useQuery({
    queryKey: debouncedKey ?? ["mateo", "availability", "check", "__disabled__"],
    queryFn: async (): Promise<NuevaCitaAvailabilityResponse> => {
      if (!doctorId || !startIso) throw new Error("Disabled");
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
    enabled: Boolean(debouncedKey) && isLoaded && Boolean(isSignedIn) && Boolean(tenantId),
    staleTime: 15_000,
    retry: 2,
  });

  const isAvailable = query.data?.status === "available";

  return { ...query, isAvailable };
}

// ── useDayStrip ────────────────────────────────────────────────────────────

interface DayStripParams {
  tenantId: string;
  // token removed — getToken() called fresh inside queryFn (T-FE-4 fix)
  doctorId: string | null;
  dateLocal: string; // YYYY-MM-DD
}

/**
 * Fetch working_hours + busy blocks for a day.
 * SC-mini-vista AC-8: paints the visual time-strip in the nueva-cita picker.
 * Disabled until doctorId is set.
 */
export function useDayStrip({
  tenantId,
  doctorId,
  dateLocal,
}: DayStripParams) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const actorHeaders = useActorHeaders();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: availabilityKeys.dayStrip(tenantId, doctorId ?? "", dateLocal),
    queryFn: async (): Promise<DayStripData> => {
      const token = await getToken();
      const params = new URLSearchParams({
        doctor_id: doctorId ?? "",
        date: dateLocal,
      });
      const raw = await vitaliaFetch<Raw>(
        `/api/v1/scheduling/availability/day-strip?${params.toString()}`,
        {
          token: token ?? "",
          tenantId,
          headers: {
            ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
            ...actorHeaders,
          },
        },
      );
      return normalizeDayStrip(raw);
    },
    enabled: Boolean(doctorId) && Boolean(dateLocal) && isLoaded && Boolean(isSignedIn) && Boolean(tenantId),
    staleTime: 30_000,
  });
}

// ── useServiceDayStrips (T-D3) ─────────────────────────────────────────────

interface ServiceDayParams {
  tenantId: string;
  serviceId: string | null;
  dateLocal: string; // YYYY-MM-DD
}

function normalizeServiceDay(raw: Raw): ServiceDayResponse {
  const doctors = Array.isArray(raw.doctors)
    ? (raw.doctors as Raw[]).map((d) => ({
        doctorId: String(d.doctor_id ?? ""),
        doctorLabel: String(d.doctor_label ?? ""),
        blocks: Array.isArray(d.blocks)
          ? (d.blocks as Raw[]).map((b) => ({
              startTime: String(b.start ?? ""),
              endTime: String(b.end ?? ""),
              kind: (b.kind as "working_hours" | "busy" | "unavailable") ?? "unavailable",
            }))
          : [],
      }))
    : [];
  return {
    serviceId: String(raw.service_id ?? ""),
    dateLocal: String(raw.date ?? ""),
    doctors,
  };
}

/**
 * useServiceDayStrips — all-doctors availability for a service+day (T-D3).
 * queryKey includes dateLocal → React Query auto-refetches when day changes.
 * doctors:[] = empty_state (no doctors assigned to service on that day).
 * Fail-closed: disabled until serviceId + dateLocal are both set.
 */
export function useServiceDayStrips({
  tenantId,
  serviceId,
  dateLocal,
}: ServiceDayParams) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const actorHeaders = useActorHeaders();
  const clinicId = useClinicId();

  return useQuery({
    queryKey: availabilityKeys.serviceDay(tenantId, serviceId ?? "", dateLocal),
    queryFn: async (): Promise<ServiceDayResponse> => {
      const token = await getToken();
      const params = new URLSearchParams({
        serviceId: serviceId ?? "",
        date: dateLocal,
      });
      const raw = await vitaliaFetch<Raw>(
        `/api/v1/scheduling/availability/service-day?${params.toString()}`,
        {
          token: token ?? "",
          tenantId,
          headers: {
            ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
            ...actorHeaders,
          },
        },
      );
      return normalizeServiceDay(raw);
    },
    enabled:
      Boolean(serviceId) &&
      Boolean(dateLocal) &&
      isLoaded &&
      Boolean(isSignedIn) &&
      Boolean(tenantId),
    staleTime: 30_000,
    retry: 2,
  });
}
