// cap: iam.luana-core-adoption
// story-origin: vitalia-fase1-s9-TBD
/**
 * lib/iam/api.ts — IAM API client for Vitalia (F1-S9 T-2).
 *
 * Consumes core endpoint GET /api/v1/iam/users/me/tenants.
 * Mounted by T-1 (BE wiring: parità nicolify/backend/src/main.py:543).
 *
 * Server-safe: uses @clerk/nextjs/server auth() — call from Server Components only.
 * Do NOT import in "use client" components.
 *
 * anti-duplication: NO new endpoint logic — consumes core auth_router already mounted.
 * spec_anchor: 03-arch-fe.md § 2.1 + 06-tickets.yaml T-2
 * HIPAA-lite: /me/tenants returns NO PHI (user identity + tenant list only).
 */

import { auth } from "@clerk/nextjs/server";
import type { TenantSchema } from "./types";

/**
 * Error codes for IamApiError.
 * - unauthorized: 401 (Clerk token missing or expired) or null token
 * - forbidden: 403 (authenticated but insufficient permissions)
 * - network_failure: DNS / timeout / AbortError
 * - unknown: any other non-2xx status
 */
export type IamErrorCode =
  | "unauthorized"
  | "forbidden"
  | "network_failure"
  | "unknown";

/**
 * Structured error thrown by fetchUserTenants on any failure.
 * Caller can narrow via `err instanceof IamApiError` + `err.code`.
 */
export class IamApiError extends Error {
  readonly code: IamErrorCode;
  readonly status?: number;

  constructor(message: string, code: IamErrorCode, status?: number) {
    super(message);
    this.name = "IamApiError";
    this.code = code;
    this.status = status;
  }
}

/**
 * Fetch the list of tenants for the currently authenticated user.
 *
 * Calls: GET /api/v1/iam/users/me/tenants
 * Auth: Clerk JWT via auth().getToken()
 * Cache: no-store (tenant list must be fresh — not cached between requests)
 *
 * Error mapping:
 *   - null Clerk token       → IamApiError(code='unauthorized')
 *   - 401 response           → IamApiError(code='unauthorized', status=401)
 *   - 403 response           → IamApiError(code='forbidden', status=403)
 *   - AbortError / TypeError → IamApiError(code='network_failure')
 *   - other non-2xx          → IamApiError(code='unknown', status=N)
 *
 * Returns [] if user has no tenants assigned (valid empty state — caller handles Q6 edge).
 *
 * @param _userId - Clerk userId (used for logging context; not sent to API)
 */
export async function fetchUserTenants(
  _userId: string,
): Promise<TenantSchema[]> {
  // 1. Obtain Clerk JWT from server-side auth
  const { getToken } = await auth();
  const token = await getToken();

  if (!token) {
    throw new IamApiError(
      "No Clerk token available — user session expired or not authenticated",
      "unauthorized",
    );
  }

  // F1 closure 2026-05-26: server-side fetch (Server Component / RSC layout.tsx) MUST
  // use INTERNAL_API_URL when running inside Docker container (FE container can't reach
  // BE via NEXT_PUBLIC_API_URL=http://127.0.0.1:8002 — that resolves to FE container itself).
  // INTERNAL_API_URL=http://vitalia_backend_dev:8002 is the Docker network internal URL.
  // Falls back to NEXT_PUBLIC_API_URL (works in dev outside container) then hard default.
  const baseUrl =
    process.env["INTERNAL_API_URL"] ??
    process.env["NEXT_PUBLIC_API_URL"] ??
    "http://localhost:8002";
  const url = `${baseUrl}/api/v1/iam/users/me/tenants`;

  // 2. Fetch user tenants with AbortController for graceful timeout
  let response: Response;
  try {
    response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });
  } catch (err: unknown) {
    // AbortError (timeout) or TypeError (network down, DNS failure)
    const name = err instanceof Error ? err.name : "";
    const isAbort = name === "AbortError";
    const isTypeError = err instanceof TypeError;
    if (isAbort || isTypeError) {
      throw new IamApiError(
        `Network failure fetching user tenants: ${err instanceof Error ? err.message : String(err)}`,
        "network_failure",
      );
    }
    throw new IamApiError(
      `Unexpected error fetching user tenants: ${err instanceof Error ? err.message : String(err)}`,
      "unknown",
    );
  }

  // 3. Map HTTP status to typed errors
  if (!response.ok) {
    if (response.status === 401) {
      throw new IamApiError(
        `Authentication failed: ${response.status} ${response.statusText}`,
        "unauthorized",
        response.status,
      );
    }
    if (response.status === 403) {
      throw new IamApiError(
        `Access forbidden: ${response.status} ${response.statusText}`,
        "forbidden",
        response.status,
      );
    }
    throw new IamApiError(
      `Failed to fetch user tenants: ${response.status} ${response.statusText}`,
      "unknown",
      response.status,
    );
  }

  // 4. Parse and return — empty array is valid (no-tenants edge case SC-8)
  return response.json() as Promise<TenantSchema[]>;
}
