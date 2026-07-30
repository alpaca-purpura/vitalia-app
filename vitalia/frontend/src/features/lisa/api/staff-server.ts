// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * staff-server.ts — SSR fetch helpers for Staff directory page.
 *
 * Server-side data fetching for Next.js Server Components.
 * Consumes auth().getToken() (Server Component Clerk pattern).
 * Returns null on error (graceful degradation — page shows client-side state).
 *
 * Per ADR-vitalia-004 § 3: Server Component fetches initial state for SSR hydration.
 * Per vitalia/.claude/rules/hipaa-lite.md: X-Clinic-ID required on all PHI endpoints.
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Data layer + 03-arch-be.md § API routes
 * downstream-regression-na: brand-local vitalia FE SSR; no cross-brand consumers
 */

import { auth } from "@clerk/nextjs/server";
import type { PaginatedDoctors, DoctorDetail } from "../types/staff.types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8002";

// ── SSR fetch: staff list (initial hydration) ──────────────────────────────────

/**
 * Fetches staff initial state for SSR hydration.
 * Returns null on auth failure or network error (client-side React Query takes over).
 */
export async function getStaffInitialState(
  tenantId: string,
  clinicId?: string | null,
): Promise<PaginatedDoctors | null> {
  try {
    const { getToken } = await auth();
    const token = await getToken();
    if (!token) return null;

    const headers: Record<string, string> = {
      Authorization: `Bearer ${token}`,
      "X-Tenant-ID": tenantId,
      "Content-Type": "application/json",
    };
    if (clinicId) {
      headers["X-Clinic-ID"] = clinicId;
    }

    const url = `${API_BASE}/api/v1/vitalia/clinics/doctors?page=1&page_size=24`;
    const res = await fetch(url, {
      headers,
      next: { revalidate: 0 }, // SSR — no cache; RQ manages client cache
    });

    if (!res.ok) return null;
    return res.json() as Promise<PaginatedDoctors>;
  } catch {
    return null;
  }
}

/**
 * Fetches single doctor detail for SSR hydration in workspace pages.
 * Returns null on auth failure or network error.
 */
export async function getDoctorInitialState(
  tenantId: string,
  doctorId: string,
  clinicId?: string | null,
): Promise<DoctorDetail | null> {
  try {
    const { getToken } = await auth();
    const token = await getToken();
    if (!token) return null;

    const headers: Record<string, string> = {
      Authorization: `Bearer ${token}`,
      "X-Tenant-ID": tenantId,
      "Content-Type": "application/json",
    };
    if (clinicId) {
      headers["X-Clinic-ID"] = clinicId;
    }

    const url = `${API_BASE}/api/v1/vitalia/clinics/doctors/${doctorId}`;
    const res = await fetch(url, {
      headers,
      next: { revalidate: 0 },
    });

    if (!res.ok) return null;
    return res.json() as Promise<DoctorDetail>;
  } catch {
    return null;
  }
}
