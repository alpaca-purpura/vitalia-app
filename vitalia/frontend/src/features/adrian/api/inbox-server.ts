// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * inbox-server.ts — SSR initial state fetch for Adrián Inbox Server Component.
 * T-3 vitalia-fase2-adrian-inbox
 *
 * Used exclusively in Server Components (app/.../adrian/inbox/page.tsx).
 * Returns empty fallback data when BE is unreachable (graceful degradation).
 * Clerk server-side token obtained via auth() from @clerk/nextjs/server.
 *
 * Pattern: mirrors mateo/api/agenda-server.ts.
 * Server Component calls getInitialInboxState() → passes result
 * as initialData to AdrianInboxView → React Query hydrates client cache.
 *
 * HIPAA-lite: no PHI persisted in SSR payload logs; tenantId scopes all queries.
 *
 * SC-7 (empty_state): returns { conversations: [], detail: null } when unavailable.
 * SC-8 (network_failure): never throws — always returns empty fallback.
 *
 * downstream-regression-na: brand-local server-side fetch; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § 1 + 06-tickets.yaml T-3
 */

import { auth } from "@clerk/nextjs/server";

// SSR runs inside the frontend Docker container. Prefer INTERNAL_API_URL
// (Docker network) when defined. Mirrors pattern in mateo/api/agenda-server.ts.
const BASE_URL =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8002";

// ── Shared types ───────────────────────────────────────────────────────────────

/** Minimal conversation summary returned by the SSR fetch */
export interface InboxConversationSummary {
  id: string;
  tenantId: string;
  clinicId: string;
  channel: string;
  handlerMode: "ai" | "human";
  proposalRequired: boolean;
  updatedAt: string;
  [key: string]: unknown; // allow additional fields from BE
}

/** SSR initial state passed to AdrianInboxView as initialData */
export interface InitialInboxState {
  conversations: InboxConversationSummary[];
  /** Conversation detail for deep-link ?conv={id}. null when not requested or failed. */
  detail: InboxConversationSummary | null;
  tenantId: string;
}

/** Options accepted by getInitialInboxState */
export interface GetInitialInboxStateOptions {
  tenantId: string;
  /** UUID of conversation to pre-load (from ?conv= searchParam). null = no deep-link. */
  convId: string | null;
  /** Inbox filter whitelist value. null = default (todos). */
  filter: string | null;
}

// ── Whitelist for inbox filter searchParam ─────────────────────────────────────

const VALID_FILTERS = new Set([
  "todos",
  "sin-leer",
  "asignadas",
  "esperando",
  "bot-activo",
  "cerradas",
]);

// ── Empty fallback ─────────────────────────────────────────────────────────────

/**
 * Empty fallback state — returned when SSR fetch fails or token is unavailable.
 * React Query will immediately refetch on mount (staleTime is 0 for this data).
 */
function emptyState(tenantId: string): InitialInboxState {
  return {
    conversations: [],
    detail: null,
    tenantId,
  };
}

// ── getInitialInboxState ───────────────────────────────────────────────────────

/**
 * Server-side initial data fetch for Adrián Inbox.
 * Called from page.tsx Server Component to enable SSR without layout shift.
 *
 * Graceful degradation (SC-7 / SC-8):
 * - Returns emptyState if not signed in (middleware handles redirect — defensive)
 * - Returns emptyState on network error (never throws)
 * - Logs warning on error (console.warn acceptable in server context)
 */
export async function getInitialInboxState({
  tenantId,
  convId,
  filter,
}: GetInitialInboxStateOptions): Promise<InitialInboxState> {
  try {
    const { getToken } = await auth();
    const token = await getToken();

    if (!token) {
      // Middleware handles redirect — this is a defensive fallback only
      return emptyState(tenantId);
    }

    // Normalise filter — only allow whitelisted values
    const safeFilter =
      filter !== null && VALID_FILTERS.has(filter) ? filter : null;

    // Fetch conversation list
    const params = new URLSearchParams();
    if (safeFilter) params.set("filter", safeFilter);
    if (convId) params.set("conv", convId);

    const listUrl = `${BASE_URL}/api/v1/vitalia/inbox/conversations${
      params.toString() ? `?${params.toString()}` : ""
    }`;

    const listResponse = await fetch(listUrl, {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        "X-Tenant-ID": tenantId,
      },
      next: { revalidate: 0 }, // Always fresh on server render
    });

    if (!listResponse.ok) {
      console.warn(
        `[inbox-server] getInitialInboxState list fetch failed: ${listResponse.status} ${listResponse.statusText}`,
        { tenantId, filter: safeFilter },
      );
      return emptyState(tenantId);
    }

    const listJson = (await listResponse.json()) as {
      conversations?: InboxConversationSummary[];
    };
    const conversations: InboxConversationSummary[] =
      listJson.conversations ?? [];

    // Optionally pre-fetch conversation detail for deep-link (SC-7: graceful degradation)
    let detail: InboxConversationSummary | null = null;
    if (convId) {
      try {
        const detailResponse = await fetch(
          `${BASE_URL}/api/v1/vitalia/inbox/conversations/${encodeURIComponent(convId)}`,
          {
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
              "X-Tenant-ID": tenantId,
            },
            next: { revalidate: 0 },
          },
        );
        if (detailResponse.ok) {
          detail =
            (await detailResponse.json()) as InboxConversationSummary;
        }
      } catch {
        // Detail pre-fetch failure is non-fatal — client will fetch on mount
        console.warn("[inbox-server] detail pre-fetch failed for convId", {
          convId,
          tenantId,
        });
      }
    }

    return { conversations, detail, tenantId };
  } catch (err) {
    // SC-8: Network error or auth error — graceful degradation
    console.warn("[inbox-server] getInitialInboxState error:", err, {
      tenantId,
    });
    return emptyState(tenantId);
  }
}
