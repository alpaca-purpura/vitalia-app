// cap: scheduling.mateo-agenda
/**
 * use-patients.ts — React Query hooks for patient typeahead + inline create.
 * T-FE-2 vitalia-fase2-mateo-nueva-cita
 *
 * ★ ANTI-EMBUDO CONTRACT (verified against T-BE-5 DTOs 2026-06-22):
 *   GET  /api/v1/crm/patients?q=&cursor=&limit=
 *        → PatientSearchResponse (items[{patient_id,name_masked,phone_masked,...}], next_cursor, total_approx)
 *   POST /api/v1/crm/patients
 *        Request: { name, phone?, email?, channel("walk_in"|"phone"|...), note? }
 *        Response: { patient_id, name_masked, phone_masked?, is_duplicate, created_at }
 *
 * ★ CHANNEL MAPPING: UI uses "walk_in"|"telefono"; BE requires "walk_in"|"phone"
 *   "telefono" → "phone" at the serializer boundary (this file).
 *
 * HIPAA-lite: PHI never in URL query params (q= is a generic token, not name/dni).
 * Dual filter: X-Clinic-ID + X-Tenant-ID required.
 *
 * EntityPicker.searchFn contract (from @luana/ui-kit):
 *   searchFn({ q, cursor, limit }) => Promise<{ items: EntityPickerItem[], nextCursor? }>
 * So useSearchPatients returns a `searchFn` that maps patient data to EntityPickerItem shape.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE hooks; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § F3 + 06-tickets.yaml T-FE-2
 */

"use client";

import { useMutation } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { vitaliaFetch } from "@/lib/fetch-client";
import { useActorHeaders } from "@/hooks/useActorHeaders";
import { useClinicId } from "@/hooks/useClinicId";
import type { EntitySearchArgs, EntitySearchResult, EntityPickerItem } from "@luana/ui-kit";

// ── Types ─────────────────────────────────────────────────────────────────────

/** UI channel values (what components use) */
type UiChannel = "walk_in" | "telefono";

/** BE channel values (what the API accepts) */
type BeChannel = "whatsapp" | "instagram" | "web" | "phone" | "walk_in" | "other";

/** Payload for inline patient create (T-FE-2 scope) */
export interface CreatePatientInlinePayload {
  name: string;
  phone: string | null;
  email: string | null;
  /** UI channel — will be mapped to BE channel before sending */
  uiChannel: UiChannel;
  note: string | null;
}

/** Normalized response from inline patient create */
export interface PatientInlineCreateResult {
  patientId: string;
  nameMasked: string;
  phoneMasked: string | null;
  /** true when BE found existing patient with same phone (RN-9) */
  isDuplicate: boolean;
}

/** EntityPickerItem extended with masked phone for display */
export interface PatientPickerItem extends EntityPickerItem {
  phoneMasked: string | null;
  channelFirst: string | null;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

type Raw = Record<string, unknown>;

/** Maps UI channel ("telefono") to BE channel ("phone"). walk_in passes through. */
function mapUiChannelToBe(uiChannel: UiChannel): BeChannel {
  return uiChannel === "telefono" ? "phone" : "walk_in";
}

function normalizePatientItem(raw: Raw): PatientPickerItem {
  return {
    id: String(raw.patient_id ?? ""),
    name: String(raw.name_masked ?? ""),
    phoneMasked: raw.phone_masked != null ? String(raw.phone_masked) : null,
    channelFirst: raw.channel_first != null ? String(raw.channel_first) : null,
  };
}

function normalizeCreateResponse(raw: Raw): PatientInlineCreateResult {
  return {
    patientId: String(raw.patient_id ?? ""),
    nameMasked: String(raw.name_masked ?? ""),
    phoneMasked: raw.phone_masked != null ? String(raw.phone_masked) : null,
    isDuplicate: Boolean(raw.is_duplicate),
  };
}

// ── Hook params ───────────────────────────────────────────────────────────────
// token removed — getToken() called fresh inside each async fn (T-FE-4 fix).

interface BaseParams {
  tenantId: string;
}

// ────────────────────────────────────────────────────────────────────────────
// useSearchPatients — builds a searchFn compatible with EntityPicker
// ────────────────────────────────────────────────────────────────────────────

/**
 * Returns a stable `searchFn` for EntityPicker (cursor-based pagination).
 * PHI never in URL — q= is a generic search token.
 * Dual filter: X-Clinic-ID mandatory.
 *
 * Note: does NOT use useQuery — the EntityPicker drives fetches internally via
 * its own state machine (debounce + infinite scroll). We just provide the async
 * function it calls.
 */
export function useSearchPatients({ tenantId }: BaseParams) {
  const { getToken } = useAuth();
  const actorHeaders = useActorHeaders();
  const clinicId = useClinicId();

  const searchFn = async (
    args: EntitySearchArgs,
  ): Promise<EntitySearchResult<PatientPickerItem>> => {
    const token = await getToken();
    const params = new URLSearchParams();
    params.set("q", args.q);
    params.set("limit", String(args.limit));
    if (args.cursor) params.set("cursor", args.cursor);

    const raw = await vitaliaFetch<{
      items: Raw[];
      next_cursor: string | null;
      total_approx: number;
    }>(`/api/v1/crm/patients?${params.toString()}`, {
      token: token ?? "",
      tenantId,
      headers: {
        ...(clinicId ? { "X-Clinic-ID": clinicId } : {}),
        ...actorHeaders,
      },
    });

    return {
      items: raw.items.map(normalizePatientItem),
      nextCursor: raw.next_cursor ?? null,
      total: raw.total_approx,
    };
  };

  return { searchFn };
}

// ────────────────────────────────────────────────────────────────────────────
// useCreatePatientInline — POST /api/v1/crm/patients
// ────────────────────────────────────────────────────────────────────────────

/**
 * Mutation: create minimal patient inline during nueva-cita flow.
 * Maps "telefono" → "phone" for the BE channel field.
 * Returns isDuplicate flag for RN-9 duplicate phone prompt.
 *
 * PHI transmitted in POST body ONLY (dual filter: X-Clinic-ID + X-Tenant-ID).
 */
export function useCreatePatientInline({ tenantId }: BaseParams) {
  const { getToken } = useAuth();
  const actorHeaders = useActorHeaders();
  const clinicId = useClinicId();

  return useMutation({
    mutationFn: async (
      payload: CreatePatientInlinePayload,
    ): Promise<PatientInlineCreateResult> => {
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
          channel: mapUiChannelToBe(payload.uiChannel),
          note: payload.note,
        }),
      });

      return normalizeCreateResponse(raw);
    },
  });
}
