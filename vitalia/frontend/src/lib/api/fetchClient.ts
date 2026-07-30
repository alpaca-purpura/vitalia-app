// cap: iam.luana-core-adoption
// story-origin: TBD
/**
 * fetchClient — Vitalia tenant+clinic aware fetch wrapper.
 *
 * Auto-injects (per HIPAA-lite dual filter):
 *   - Authorization: Bearer <token>   (Clerk JWT)
 *   - X-Tenant-ID: <tenantId>          (our luana-core-iam tenant ID, from user.publicMetadata)
 *   - X-Clinic-ID: <clinicId>          (HIPAA-lite dual filter — vitalia-specific, from user.publicMetadata)
 *   - Content-Type: application/json
 *
 * Design: plain async function (NOT a React hook).
 * Caller pattern in React Query queryFn:
 *   1. useAuth() → getToken()
 *   2. useTenantStore() → activeTenant.id (our luana-core-iam tenant_id)
 *   3. useClinicId() → clinicId (from user.publicMetadata.clinicId, written by luana-core-iam)
 *   4. queryFn calls fetchClient({ token, tenantId, clinicId })
 *
 * Per .claude/rules/tenant-isolation.md: EVERY request MUST include X-Tenant-ID.
 * Per vitalia/.claude/rules/hipaa-lite.md: EVERY PHI request MUST also include X-Clinic-ID.
 *
 * NOTE: This file intentionally does NOT use React hooks.
 * NEVER manually inject X-Tenant-ID in Client Components — this file handles it.
 *
 * Per MEMORY.md::no-clerk-organizations (2026-05-20):
 *   tenant_id and clinic_id are OUR data from luana-core-iam, NOT from Clerk Organizations.
 *   Clerk is used only as an identity provider (JWT + user.publicMetadata storage).
 */

export class ApiError extends Error {
  readonly status: number;
  readonly statusText: string;
  readonly body: unknown;

  constructor(response: Response, body?: unknown) {
    super(`API error ${response.status}: ${response.statusText}`);
    this.name = "ApiError";
    this.status = response.status;
    this.statusText = response.statusText;
    this.body = body;
  }
}

export interface FetchClientOptions extends Omit<RequestInit, "headers"> {
  /** Clerk JWT obtained via useAuth().getToken() */
  token: string;
  /** Luana-core-iam tenant ID (X-Tenant-ID header). From useTenantStore().activeTenant.id or user.publicMetadata.tenantId. NOT a Clerk organization ID. */
  tenantId: string;
  /** Clinic ID for HIPAA-lite dual filter (X-Clinic-ID header). From useClinicId() → user.publicMetadata.clinicId (luana-core-iam). Required for PHI endpoints. */
  clinicId?: string | null;
  /** Additional headers to merge */
  headers?: Record<string, string>;
  /** Abort signal timeout in ms (default: 30000) */
  timeoutMs?: number;
}

/**
 * Tenant + clinic aware fetch wrapper.
 *
 * @throws ApiError on non-2xx response
 */
export async function fetchClient<T>(
  url: string,
  options: FetchClientOptions,
): Promise<T> {
  const {
    token,
    tenantId,
    clinicId,
    headers: customHeaders,
    timeoutMs = 30000,
    ...rest
  } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const mergedHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...customHeaders,
    Authorization: `Bearer ${token}`,
    "X-Tenant-ID": tenantId,
  };

  // HIPAA-lite dual filter: inject clinic ID when available
  if (clinicId) {
    mergedHeaders["X-Clinic-ID"] = clinicId;
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...rest,
      headers: mergedHeaders,
      signal: rest.signal ?? controller.signal,
    });
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      body = null;
    }
    throw new ApiError(response, body);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}
