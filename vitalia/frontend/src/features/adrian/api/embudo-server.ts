// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * embudo-server.ts — Server-side initial state fetch for Embudo board page.
 * T-FE-2 vitalia-fase2-adrian-embudo
 *
 * Called by Server Component page.tsx to hydrate AdrianEmbudoView.
 * Uses auth() from @clerk/nextjs/server for server-side Clerk auth.
 * Graceful degradation: returns null on error (client re-fetches).
 *
 * IMPORTANT: This file MUST NOT include "use client" — it runs on the server only.
 * Do NOT import this in any "use client" component.
 *
 * Pattern mirrors: features/adrian/api/inbox-server.ts (getInitialInboxState)
 *
 * spec_anchor: 03-arch-fe.md § Routing (Server Component + SSR)
 * downstream-regression-na: brand-local vitalia FE server
 */
import { auth } from "@clerk/nextjs/server";
import { keysToCamel } from "@/lib/api/keys-to-camel";
import type { BoardResponse, BoardFilters } from "../types/embudo.types";

const BASE_URL =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8002";

export interface GetEmbudoBoardInitialStateOptions {
  tenantId: string;
  filters?: BoardFilters;
}

/**
 * getEmbudoBoardInitialState — SSR fetch for the board.
 *
 * Returns null on any error (graceful degradation per ADR-vitalia-004 § 3.3).
 * The client root (AdrianEmbudoView) will re-fetch on mount if null.
 */
export async function getEmbudoBoardInitialState({
  tenantId,
  filters = {},
}: GetEmbudoBoardInitialStateOptions): Promise<BoardResponse | null> {
  try {
    const { getToken } = await auth();
    const token = await getToken();
    if (!token) return null;

    const params = new URLSearchParams();
    if (filters.view) params.set("view", filters.view);
    if (filters.sort) params.set("sort", filters.sort);

    const qs = params.toString();
    const url = `${BASE_URL}/api/v1/crm/board${qs ? `?${qs}` : ""}`;

    const res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Tenant-ID": tenantId,
        "Content-Type": "application/json",
      },
      next: { revalidate: 30 },
    });

    if (!res.ok) return null;
    // BE crm DTOs son snake_case (sin alias); el view-model FE es camelCase.
    return keysToCamel<BoardResponse>(await res.json());
  } catch {
    return null;
  }
}
