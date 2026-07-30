// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * servicios-server.ts — SSR fetch helpers for the Servicios pages.
 *
 * Server Component fetches (ADR-vitalia-004 § 3). Returns null on error
 * (graceful degradation — the client-side React Query takes over).
 *
 * ★ WIRE = snake_case (offer module). API_BASE is the ABSOLUTE NEXT_PUBLIC_API_URL
 *   here (server-to-server, no CORS); the client base is relative (servicios.ts).
 *
 * Catalog is NOT PHI (RN-13) → no X-Clinic-ID on the list fetch.
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: 03-arch-fe.md § Data layer + 03-arch-be.md § API routes
 * downstream-regression-na: brand-local vitalia FE SSR; no cross-brand consumers
 */

import { auth } from "@clerk/nextjs/server";
import type {
  ServiceDetail,
  ServiceListResponse,
  ServiciosView,
} from "../types/servicios.types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8002";

export interface ServiciosInitialState {
  list: ServiceListResponse | null;
  view: ServiciosView;
}

/**
 * Fetches the initial catalog list for SSR hydration. The same default
 * (unfiltered) list seeds both the catalogo grid and the escalera grouping.
 */
export async function getServiciosInitialState({
  tenantId,
  view,
}: {
  tenantId: string;
  view: ServiciosView;
}): Promise<ServiciosInitialState> {
  try {
    const { getToken } = await auth();
    const token = await getToken();
    if (!token) return { list: null, view };

    const headers: Record<string, string> = {
      Authorization: `Bearer ${token}`,
      "X-Tenant-ID": tenantId,
      "Content-Type": "application/json",
    };

    // BE paginates by cursor (no page_size); the first page seeds both the
    // catalogo grid and the escalera grouping. Spanish route `/servicios`.
    const url = `${API_BASE}/api/v1/offer/servicios`;
    const res = await fetch(url, { headers, next: { revalidate: 0 } });
    if (!res.ok) return { list: null, view };
    const list = (await res.json()) as ServiceListResponse;
    return { list, view };
  } catch {
    return { list: null, view };
  }
}

/**
 * getServicioDetail — SSR fetch of one service's full detail for the workspace
 * layout (T-7). The catalog detail is NOT PHI (RN-13) → X-Tenant-ID only, no
 * X-Clinic-ID / X-User-ID. Returns null on any error so the layout renders the
 * client-side fallback (React Query re-fetches via useServicioDetail).
 */
export async function getServicioDetail({
  tenantId,
  offerId,
}: {
  tenantId: string;
  offerId: string;
}): Promise<ServiceDetail | null> {
  try {
    const { getToken } = await auth();
    const token = await getToken();
    if (!token) return null;

    const headers: Record<string, string> = {
      Authorization: `Bearer ${token}`,
      "X-Tenant-ID": tenantId,
      "Content-Type": "application/json",
    };

    const url = `${API_BASE}/api/v1/offer/servicios/${offerId}`;
    const res = await fetch(url, { headers, next: { revalidate: 0 } });
    if (!res.ok) return null;
    return (await res.json()) as ServiceDetail;
  } catch {
    return null;
  }
}
