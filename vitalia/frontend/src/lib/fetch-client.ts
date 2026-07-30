// cap: iam.luana-core-adoption
// story-origin: TBD
/**
 * vitaliaFetch — tenant-aware fetch wrapper for Vitalia React Query hooks.
 *
 * Design decision: fetchClient is NOT a React hook. It is a plain async function
 * that receives token + tenantId as params (already resolved by the React Query
 * queryFn that calls useAuth() before invoking fetchClient).
 *
 * This pattern allows:
 * 1. React hooks call useAuth() → get token + tenantId
 * 2. React Query queryFn passes token + tenantId to vitaliaFetch
 * 3. vitaliaFetch injects X-Tenant-ID header automatically
 *
 * Per .claude/rules/tenant-isolation.md:
 * - Every request MUST include X-Tenant-ID
 * - NEVER hardcode tenantId
 * - NEVER skip Authorization header
 */

export class ApiError extends Error {
  status: number;
  statusText: string;

  constructor(response: Response) {
    super(`API error ${response.status}: ${response.statusText}`);
    this.name = "ApiError";
    this.status = response.status;
    this.statusText = response.statusText;
  }
}

export interface VitaliaFetchOptions extends Omit<RequestInit, "headers"> {
  token: string;
  tenantId: string;
  headers?: Record<string, string>;
}

/**
 * Tenant-aware fetch wrapper.
 * Auto-injects:
 * - Authorization: Bearer <token>
 * - X-Tenant-ID: <tenantId>
 * - Content-Type: application/json
 *
 * @throws ApiError on non-2xx response
 */
export async function vitaliaFetch<T>(
  url: string,
  options: VitaliaFetchOptions,
): Promise<T> {
  const { token, tenantId, headers: customHeaders, ...rest } = options;

  const response = await fetch(url, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...customHeaders,
      Authorization: `Bearer ${token}`,
      "X-Tenant-ID": tenantId,
    },
  });

  if (!response.ok) {
    throw new ApiError(response);
  }

  return response.json() as Promise<T>;
}
