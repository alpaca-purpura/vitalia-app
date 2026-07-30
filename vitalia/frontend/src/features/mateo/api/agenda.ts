// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
/**
 * agenda.ts — React Query v5 hooks for Valeria Agenda feature.
 * T-12 vitalia-fase2-valeria-agenda
 *
 * Query key factory (stable references, per React Query v5 best practices):
 *   agendaKeys.grid(tenantId, view, date, filters?)
 *   agendaKeys.aggregates(tenantId, dateFrom, dateTo)
 *   agendaKeys.detail(tenantId, appointmentId)
 *
 * Polling: useAgendaGrid polls every 30 seconds (refetchInterval: 30_000).
 * Tenant isolation: every request passes tenantId via vitaliaFetch (X-Tenant-ID header).
 * HIPAA-lite: PHI is masked server-side — FE only receives masked strings.
 *
 * ★ Actor headers (vitalia-bugfix-agenda-actor-headers-422, 2026-06-15):
 *   The scheduling/agenda endpoints (agenda_router.py) REQUIRE the HIPAA-lite dual filter
 *   + audit actor: X-Tenant-ID + X-Clinic-ID + X-User-ID, and gate RBAC on X-User-Role
 *   (ALLOWED_PHI_ROLES). Sending only X-Tenant-ID → 422 (Field required) + empty grid.
 *   X-Clinic-ID comes from useClinicId(); X-User-ID (DB UUID) + X-User-Role (per-tenant)
 *   come from the shared useActorHeaders() hook (lifted from features/lisa — FSD-Lite, no
 *   cross-feature import). PHI queries gate on a non-empty X-User-ID (avoids the 422 race
 *   of firing before /me resolves).
 *
 * downstream-regression-na: brand-local FE hooks; no cross-brand consumers
 * spec_anchor: 03-arch.md § 5.1 + 06-tickets.yaml T-12
 */

"use client";

import { useAuth } from "@clerk/nextjs";
import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { vitaliaFetch } from "@/lib/fetch-client";
import { useClinicId } from "@/hooks/useClinicId";
import { useActorHeaders } from "@/hooks/useActorHeaders";
import { normalizeAgendaGridResponse, normalizeAppointmentDetail } from "./normalize-agenda";
import type {
  AgendaGridResponse,
  AgendaView,
  AgendaFilter,
  Appointment,
  FiscalDocument,
} from "../types/agenda.types";
import type {
  AgendaGridResponseDTO,
  ChargeResponseDTO,
  CreateAppointmentRequestDTO,
  PatchAppointmentRequestDTO,
  NotifyRequestDTO,
} from "../types/agenda-schema";

// ── 1. Query key factory ───────────────────────────────────────────────────────

/**
 * Stable query key factory — prevents key typos and enables targeted invalidation.
 * Using tuple format per React Query v5 best practices.
 */
export const agendaKeys = {
  all: (tenantId: string) => ["agenda", tenantId] as const,
  grid: (
    tenantId: string,
    view: AgendaView,
    date: string,
    filters?: AgendaFilter | null,
  ) => ["agenda", "grid", tenantId, view, date, filters ?? null] as const,
  aggregates: (tenantId: string, dateFrom: string, dateTo: string) =>
    ["agenda", "aggregates", tenantId, dateFrom, dateTo] as const,
  detail: (tenantId: string, appointmentId: string) =>
    ["agenda", "detail", tenantId, appointmentId] as const,
} as const;

// ── 2. Base URL helper ─────────────────────────────────────────────────────────

const BASE = "/api/v1/scheduling";
const PAYMENTS_BASE = "/api/v1/payments";
const FISCAL_BASE = "/api/v1/fiscal";
const NOTIFY_BASE = "/api/v1/notify";

// ── Actor headers helper ────────────────────────────────────────────────────────

/**
 * useAgendaActorHeaders — merges the HIPAA-lite headers every scheduling/agenda call
 * needs beyond X-Tenant-ID (which vitaliaFetch injects): X-Clinic-ID + X-User-ID + X-User-Role.
 * Returns the merged record + a `ready` flag (true once X-User-ID resolved) so PHI queries
 * can gate their `enabled` on it (avoids the 422 race of firing before /me resolves).
 */
function useAgendaActorHeaders(): { headers: Record<string, string>; ready: boolean } {
  const clinicId = useClinicId();
  const actorHeaders = useActorHeaders();
  const headers: Record<string, string> = {
    ...actorHeaders,
    ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
  };
  return { headers, ready: Boolean(actorHeaders["X-User-ID"]) };
}

// ── 3. useAgendaGrid — polling hook for calendar grid ─────────────────────────

export interface UseAgendaGridOptions {
  tenantId: string;
  view: AgendaView;
  date: string;
  /** Active preset filter chip — null = no filter. */
  presetFilter?: AgendaFilter | null;
  /** React Query extra options (pass placeholderData for SSR hydration). */
  queryOptions?: Partial<UseQueryOptions<AgendaGridResponseDTO>>;
}

/**
 * Fetches agenda grid slots. Polls every 30 seconds.
 * Passes initialData / placeholderData from Server Component for SSR hydration.
 */
export function useAgendaGrid({
  tenantId,
  view,
  date,
  presetFilter = null,
  queryOptions,
}: UseAgendaGridOptions) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const { headers, ready } = useAgendaActorHeaders();

  return useQuery<AgendaGridResponseDTO>({
    queryKey: agendaKeys.grid(tenantId, view, date, presetFilter),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      const params = new URLSearchParams({ view, date });
      if (presetFilter) params.set("preset_filter", presetFilter);

      // BE returns snake_case + engine enums; normalize → camelCase DTO the grid reads.
      const raw = await vitaliaFetch<unknown>(
        `${BASE}/agenda/grid?${params.toString()}`,
        { token, tenantId, headers },
      );
      return normalizeAgendaGridResponse(raw) as AgendaGridResponseDTO;
    },
    // Gate until X-User-ID (from /me) resolved — firing before it sends X-User-ID:"" → 422.
    enabled: isLoaded && isSignedIn === true && ready,
    refetchInterval: 30_000,
    staleTime: 25_000,
    ...queryOptions,
  });
}

// ── 4. useAgendaAggregates ────────────────────────────────────────────────────

export interface AgendaAggregatesResponse {
  totalSlots: number;
  pendingPayment: number;
  totalRevenueCents: number;
  currency: string;
  noShows: number;
  dateFrom: string;
  dateTo: string;
}

export interface UseAgendaAggregatesOptions {
  tenantId: string;
  dateFrom: string;
  dateTo: string;
}

export function useAgendaAggregates({
  tenantId,
  dateFrom,
  dateTo,
}: UseAgendaAggregatesOptions) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const { headers, ready } = useAgendaActorHeaders();

  return useQuery<AgendaAggregatesResponse>({
    queryKey: agendaKeys.aggregates(tenantId, dateFrom, dateTo),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      const params = new URLSearchParams({ date_from: dateFrom, date_to: dateTo });

      return vitaliaFetch<AgendaAggregatesResponse>(
        `${BASE}/agenda/aggregates?${params.toString()}`,
        { token, tenantId, headers },
      );
    },
    // Gate until X-User-ID (from /me) resolved — firing before it sends X-User-ID:"" → 422.
    enabled: isLoaded && isSignedIn === true && ready,
    staleTime: 60_000,
  });
}

// ── 5. useAppointmentDetail ───────────────────────────────────────────────────

export interface UseAppointmentDetailOptions {
  tenantId: string;
  appointmentId: string | null;
  enabled?: boolean;
}

export function useAppointmentDetail({
  tenantId,
  appointmentId,
  enabled = true,
}: UseAppointmentDetailOptions) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const { headers, ready } = useAgendaActorHeaders();

  return useQuery<Appointment>({
    queryKey: agendaKeys.detail(tenantId, appointmentId ?? ""),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      if (!appointmentId) throw new Error("appointmentId is required");

      // BE returns snake_case + engine enums; normalize → the camelCase Appointment the drawer reads.
      const raw = await vitaliaFetch<unknown>(
        `${BASE}/appointments/${appointmentId}`,
        { token, tenantId, headers },
      );
      return normalizeAppointmentDetail(raw);
    },
    // Gate until X-User-ID (from /me) resolved — firing before it sends X-User-ID:"" → 422.
    enabled: isLoaded && isSignedIn === true && !!appointmentId && enabled && ready,
    staleTime: 30_000,
  });
}

// ── 6. useCreateAppointment ───────────────────────────────────────────────────

export interface CreateAppointmentMutationContext {
  tenantId: string;
}

export function useCreateAppointment(tenantId: string) {
  const { getToken } = useAuth();
  const { headers } = useAgendaActorHeaders();
  const queryClient = useQueryClient();

  return useMutation<AgendaGridResponse, Error, CreateAppointmentRequestDTO>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      return vitaliaFetch<AgendaGridResponse>(`${BASE}/appointments`, {
        method: "POST",
        token,
        tenantId,
        headers,
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      // Invalidate all grid queries for this tenant
      void queryClient.invalidateQueries({ queryKey: agendaKeys.all(tenantId) });
    },
  });
}

// ── 7. usePatchAppointmentStatus ──────────────────────────────────────────────

export interface PatchAppointmentVariables {
  appointmentId: string;
  payload: PatchAppointmentRequestDTO;
}

export function usePatchAppointmentStatus(tenantId: string) {
  const { getToken } = useAuth();
  const { headers } = useAgendaActorHeaders();
  const queryClient = useQueryClient();

  return useMutation<Appointment, Error, PatchAppointmentVariables>({
    mutationFn: async ({ appointmentId, payload }) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      return vitaliaFetch<Appointment>(
        `${BASE}/appointments/${appointmentId}`,
        {
          method: "PATCH",
          token,
          tenantId,
          headers,
          body: JSON.stringify(payload),
        },
      );
    },
    onSuccess: (_, { appointmentId }) => {
      // Invalidate grid + specific appointment detail
      void queryClient.invalidateQueries({ queryKey: agendaKeys.all(tenantId) });
      void queryClient.invalidateQueries({
        queryKey: agendaKeys.detail(tenantId, appointmentId),
      });
    },
  });
}

// ── 8. useChargeAppointment ───────────────────────────────────────────────────

export interface ChargeAppointmentVariables {
  appointmentId: string;
  /** ChargeRequest payload from ChargeRequestSchema */
  payload: Record<string, unknown>;
  /** UUID v4 idempotency key — caller must generate before mutation */
  idempotencyKey: string;
}

export function useChargeAppointment(tenantId: string) {
  const { getToken } = useAuth();
  const { headers: actorHeaders } = useAgendaActorHeaders();
  const queryClient = useQueryClient();

  return useMutation<ChargeResponseDTO, Error, ChargeAppointmentVariables>({
    mutationFn: async ({ appointmentId, payload, idempotencyKey }) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      return vitaliaFetch<ChargeResponseDTO>(
        `${PAYMENTS_BASE}/charge`,
        {
          method: "POST",
          token,
          tenantId,
          // Merge actor headers (X-Clinic-ID + X-User-ID + X-User-Role) WITH the
          // per-call idempotency key — payments/charge requires the dual filter + audit actor.
          headers: {
            ...actorHeaders,
            "X-Idempotency-Key": idempotencyKey,
          },
          body: JSON.stringify({ appointment_id: appointmentId, ...payload }),
        },
      );
    },
    onSuccess: (_, { appointmentId }) => {
      // Invalidate grid (payment status badge changes) + appointment detail
      void queryClient.invalidateQueries({ queryKey: agendaKeys.all(tenantId) });
      void queryClient.invalidateQueries({
        queryKey: agendaKeys.detail(tenantId, appointmentId),
      });
    },
  });
}

// ── 9. useEmitFiscalDoc ───────────────────────────────────────────────────────

export interface EmitFiscalDocVariables {
  paymentId: string;
  docType: "factura" | "boleta" | "ticket";
}

export function useEmitFiscalDoc(tenantId: string) {
  const { getToken } = useAuth();
  const { headers } = useAgendaActorHeaders();
  const queryClient = useQueryClient();

  return useMutation<FiscalDocument, Error, EmitFiscalDocVariables>({
    mutationFn: async ({ paymentId, docType }) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      return vitaliaFetch<FiscalDocument>(
        `${FISCAL_BASE}/emit`,
        {
          method: "POST",
          token,
          tenantId,
          headers,
          body: JSON.stringify({ payment_id: paymentId, doc_type: docType }),
        },
      );
    },
    onSuccess: () => {
      // Invalidate all agenda queries — fiscal status may show in grid
      void queryClient.invalidateQueries({ queryKey: agendaKeys.all(tenantId) });
    },
  });
}

// ── 10. useSendReminder ───────────────────────────────────────────────────────

export interface SendReminderResponse {
  messageId: string;
  channel: string;
  sentAt: string;
}

export function useSendReminder(tenantId: string) {
  const { getToken } = useAuth();
  const { headers } = useAgendaActorHeaders();

  return useMutation<SendReminderResponse, Error, NotifyRequestDTO>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      return vitaliaFetch<SendReminderResponse>(
        `${NOTIFY_BASE}/reminder`,
        {
          method: "POST",
          token,
          tenantId,
          headers,
          body: JSON.stringify(payload),
        },
      );
    },
    // No cache invalidation needed — reminders don't affect the grid state
  });
}
