// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
/**
 * agenda-server.ts — SSR initial state fetch for Valeria Agenda Server Component.
 * T-12 vitalia-fase2-valeria-agenda
 *
 * Used exclusively in Server Components (page.tsx).
 * Returns empty fallback data when BE is unreachable (graceful degradation).
 * Clerk server-side token is obtained via auth() from @clerk/nextjs/server.
 *
 * Pattern: Server Component calls getInitialAgendaState() → passes result
 * as placeholderData to MateoAgendaView → React Query hydrates client cache.
 *
 * ★ Actor headers (vitalia-bugfix-agenda-actor-headers-422, 2026-06-15):
 *   /scheduling/agenda/grid REQUIRES the HIPAA-lite dual filter + audit actor
 *   (X-Tenant-ID + X-Clinic-ID + X-User-ID) and gates RBAC on X-User-Role. SSR sending
 *   only X-Tenant-ID → 422 → emptyGrid every render (masking the bug). X-Clinic-ID comes
 *   from session.sessionClaims["clinic_id"] (resolved in page.tsx); X-User-ID (DB UUID) +
 *   X-User-Role (per-tenant) resolve server-side via GET /api/v1/iam/users/me (the handler
 *   resolves both from the X-Tenant-ID header — dependencies.py § per-tenant role). Still
 *   graceful: missing actor context → emptyGrid (no throw, no layout shift).
 *
 * downstream-regression-na: brand-local server-side fetch; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.3 + 06-tickets.yaml T-12 (A1)
 */

import { auth, clerkClient } from "@clerk/nextjs/server";
import type { AgendaGridResponseDTO } from "../types/agenda-schema";
import type { AgendaView } from "../types/agenda.types";
import { normalizeAgendaGridResponse } from "./normalize-agenda";

// SSR runs inside the frontend Docker container: NEXT_PUBLIC_API_URL points to
// `http://127.0.0.1:8002` (which the host browser can reach) but resolves to the
// frontend container itself, not the backend. Prefer INTERNAL_API_URL
// (`http://vitalia_backend_dev:8002` — Docker network) when defined.
// Mirrors the pattern in vitalia/frontend/src/lib/iam/api.ts.
const BASE_URL =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8002";

// ── Empty fallback ─────────────────────────────────────────────────────────────

/**
 * Empty fallback grid — returned when SSR fetch fails or token is unavailable.
 * React Query will immediately refetch on mount (staleTime=25_000, initialData is stale).
 */
function emptyGrid(
  tenantId: string,
  view: AgendaView,
  date: string,
): AgendaGridResponseDTO {
  return {
    view,
    dateFrom: date,
    dateTo: date,
    slots: [],
    serverTime: new Date().toISOString(),
    clinicId: "",
    tenantId,
  };
}

// ── Server-side actor context resolution ────────────────────────────────────────

/** Engine GET /api/v1/iam/users/me response shape (DB UUID id + per-tenant role). */
interface MeResponse {
  id: string;
  role: string;
}

/**
 * Resolves the X-User-ID (DB UUID) + X-User-Role (per-tenant) headers server-side
 * by calling GET /api/v1/iam/users/me with the Clerk token + X-Tenant-ID (the handler
 * resolves both from the tenant context — same source as the client useActorHeaders).
 *
 * Graceful: returns {} on any failure → caller falls back to emptyGrid (no throw).
 */
async function resolveActorHeaders(
  token: string,
  tenantId: string,
): Promise<Record<string, string>> {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/iam/users/me`, {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        "X-Tenant-ID": tenantId,
      },
      next: { revalidate: 0 },
    });
    if (!res.ok) return {};
    const me = (await res.json()) as MeResponse;
    const headers: Record<string, string> = {};
    if (me.id) headers["X-User-ID"] = me.id;
    if (me.role) headers["X-User-Role"] = me.role;
    return headers;
  } catch {
    return {};
  }
}

/**
 * Resolves X-Clinic-ID server-side from the Clerk user's publicMetadata.clinicId —
 * the SAME canonical source as the client useClinicId(). Read via the Clerk backend
 * API (clerkClient) because the dev JWT template does NOT inject custom claims, so
 * session.sessionClaims has no clinic_id / public_metadata (the page-claim path was the
 * bug). `userId` comes from auth(); a caller-provided clinicId (e.g. a claim) wins if set.
 *
 * Graceful: returns null on any failure → caller falls back to emptyGrid.
 */
async function resolveClinicId(
  userId: string | null,
  override?: string | null,
): Promise<string | null> {
  if (override) return override;
  if (!userId) return null;
  try {
    const client = await clerkClient();
    const user = await client.users.getUser(userId);
    const clinicId = (user.publicMetadata as Record<string, unknown>)["clinicId"];
    return typeof clinicId === "string" && clinicId.length > 0 ? clinicId : null;
  } catch {
    return null;
  }
}

// ── getInitialAgendaState ──────────────────────────────────────────────────────

export interface GetInitialAgendaStateOptions {
  tenantId: string;
  view: string;
  date: string;
  presetFilter: string | null;
  /** X-Clinic-ID — from session.sessionClaims["clinic_id"], resolved in page.tsx. */
  clinicId?: string | null;
}

/**
 * Server-side initial data fetch for agenda grid.
 * Called from page.tsx Server Component to enable SSR without layout shift.
 *
 * Graceful degradation:
 * - Returns emptyGrid if not signed in (middleware handles redirect, this is defensive)
 * - Returns emptyGrid on network error (never throws)
 * - Logs warning on error (structlog pattern — console.warn acceptable in server context)
 */
export async function getInitialAgendaState({
  tenantId,
  view,
  date,
  presetFilter,
  clinicId,
}: GetInitialAgendaStateOptions): Promise<AgendaGridResponseDTO> {
  const normalizedView: AgendaView = isAgendaView(view) ? view : "semana";

  try {
    const { getToken, userId } = await auth();
    const token = await getToken();

    if (!token) {
      // Middleware should handle redirect — this is defensive fallback
      return emptyGrid(tenantId, normalizedView, date);
    }

    // Resolve the full HIPAA-lite actor context server-side. The grid endpoint REQUIRES
    // X-Clinic-ID + X-User-ID (+ RBAC X-User-Role); sending only X-Tenant-ID → 422 → empty
    // grid (the bug this fixes). X-User-ID/Role come from /me; X-Clinic-ID from the Clerk
    // user's publicMetadata.clinicId (the page-passed `clinicId` overrides if present).
    const [actorHeaders, resolvedClinicId] = await Promise.all([
      resolveActorHeaders(token, tenantId),
      resolveClinicId(userId, clinicId),
    ]);

    const params = new URLSearchParams({ view: normalizedView, date });
    if (presetFilter) params.set("preset_filter", presetFilter);

    const response = await fetch(
      `${BASE_URL}/api/v1/scheduling/agenda/grid?${params.toString()}`,
      {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
          ...(resolvedClinicId ? { "X-Clinic-ID": resolvedClinicId } : {}),
          ...actorHeaders,
        },
        // Server-side fetch: no need for AbortController — Next.js handles timeouts
        next: { revalidate: 0 }, // Always fresh on server render
      },
    );

    if (!response.ok) {
      console.warn(
        `[agenda-server] getInitialAgendaState failed: ${response.status} ${response.statusText}`,
        { tenantId, view: normalizedView, date },
      );
      return emptyGrid(tenantId, normalizedView, date);
    }

    // The grid BE returns snake_case + engine enum values; normalize → the camelCase DTO the
    // components read (raw cast was the bug: undefined fields → blank grid). Idempotent.
    return normalizeAgendaGridResponse(await response.json()) as AgendaGridResponseDTO;
  } catch (err) {
    // Network error or auth error — graceful degradation
    console.warn("[agenda-server] getInitialAgendaState error:", err, {
      tenantId,
      view: normalizedView,
      date,
    });
    return emptyGrid(tenantId, normalizedView, date);
  }
}

// ── Type guard ─────────────────────────────────────────────────────────────────

function isAgendaView(value: string): value is AgendaView {
  return value === "dia" || value === "semana" || value === "mes";
}
