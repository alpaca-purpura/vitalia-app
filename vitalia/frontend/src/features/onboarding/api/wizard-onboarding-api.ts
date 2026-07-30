// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
/**
 * wizard-onboarding-api.ts — Typed API wrappers for wizard onboarding endpoints.
 *
 * Uses vitaliaFetch (requires explicit token + tenantId).
 * Auto-injects Authorization + X-Tenant-ID headers.
 *
 * Endpoints (shipped in T-onboarding-3):
 *   POST   /api/v1/vitalia/wizard/drafts              — start draft
 *   GET    /api/v1/vitalia/wizard/drafts/{id}          — get draft state
 *   POST   /api/v1/vitalia/wizard/drafts/{id}/extract  — extract from URL/doc
 *   POST   /api/v1/vitalia/wizard/drafts/{id}/slots/{slotId}/confirm — confirm slot
 *   POST   /api/v1/vitalia/wizard/drafts/{id}/simulate — simulate voice preview
 *   POST   /api/v1/vitalia/wizard/drafts/{id}/complete — complete onboarding
 *   GET    /api/v1/vitalia/wizard/drafts/{id}/stream   — SSE stream (raw EventSource)
 *
 * Per tenant-isolation.md: fetchClient auto-injects X-Tenant-ID from Clerk.
 * NEVER manually pass X-Tenant-ID in Client Components.
 *
 * downstream-regression-na: brand-local FE API; no cross-brand consumers
 */

import { vitaliaFetch } from "@/lib/fetch-client";
import type {
  StartDraftRequest,
  StartDraftResponse,
  GetDraftResponse,
  ExtractContextRequest,
  ExtractContextResponse,
  ConfirmSlotRequest,
  ConfirmSlotResponse,
  SimulateVoiceRequest,
  SimulateVoiceResponse,
  CompleteOnboardingRequest,
  CompleteOnboardingResponse,
} from "../types/wizard-onboarding.types";

/** Base path for wizard API */
const WIZARD_BASE = "/api/v1/vitalia/wizard";

// ---------------------------------------------------------------------------
// Auth context type (resolved by hooks before calling these fns)
// ---------------------------------------------------------------------------

export interface WizardApiAuth {
  token: string;
  tenantId: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * Start a new wizard draft (or resume by returning an in-progress draft).
 * POST /api/v1/vitalia/wizard/drafts
 */
export async function startDraft(
  auth: WizardApiAuth,
  payload: StartDraftRequest,
): Promise<StartDraftResponse> {
  return vitaliaFetch<StartDraftResponse>(`${WIZARD_BASE}/drafts`, {
    method: "POST",
    token: auth.token,
    tenantId: auth.tenantId,
    body: JSON.stringify(payload),
  });
}

/**
 * Get current draft state + slots + progress.
 * GET /api/v1/vitalia/wizard/drafts/{draftId}
 */
export async function getDraft(
  auth: WizardApiAuth,
  draftId: string,
): Promise<GetDraftResponse> {
  return vitaliaFetch<GetDraftResponse>(
    `${WIZARD_BASE}/drafts/${encodeURIComponent(draftId)}`,
    {
      method: "GET",
      token: auth.token,
      tenantId: auth.tenantId,
    },
  );
}

/**
 * Extract tenant context from URL or text content.
 * POST /api/v1/vitalia/wizard/drafts/{draftId}/extract
 */
export async function extractContext(
  auth: WizardApiAuth,
  draftId: string,
  payload: ExtractContextRequest,
): Promise<ExtractContextResponse> {
  return vitaliaFetch<ExtractContextResponse>(
    `${WIZARD_BASE}/drafts/${encodeURIComponent(draftId)}/extract`,
    {
      method: "POST",
      token: auth.token,
      tenantId: auth.tenantId,
      body: JSON.stringify(payload),
    },
  );
}

/**
 * Confirm a slot value (user-entered or user-corrected extracted value).
 * POST /api/v1/vitalia/wizard/drafts/{draftId}/slots/{slotId}/confirm
 */
export async function confirmSlot(
  auth: WizardApiAuth,
  draftId: string,
  payload: ConfirmSlotRequest,
): Promise<ConfirmSlotResponse> {
  return vitaliaFetch<ConfirmSlotResponse>(
    `${WIZARD_BASE}/drafts/${encodeURIComponent(draftId)}/slots/${encodeURIComponent(payload.slotId)}/confirm`,
    {
      method: "POST",
      token: auth.token,
      tenantId: auth.tenantId,
      body: JSON.stringify(payload),
    },
  );
}

/**
 * Simulate voice preview (debounced from LivePreview components).
 * POST /api/v1/vitalia/wizard/drafts/{draftId}/simulate
 */
export async function simulateVoice(
  auth: WizardApiAuth,
  draftId: string,
  payload: SimulateVoiceRequest,
): Promise<SimulateVoiceResponse> {
  return vitaliaFetch<SimulateVoiceResponse>(
    `${WIZARD_BASE}/drafts/${encodeURIComponent(draftId)}/simulate`,
    {
      method: "POST",
      token: auth.token,
      tenantId: auth.tenantId,
      body: JSON.stringify(payload),
    },
  );
}

/**
 * Complete onboarding — compile + commit brand studio draft + mark tenant onboarded.
 * POST /api/v1/vitalia/wizard/drafts/{draftId}/complete
 */
export async function completeOnboarding(
  auth: WizardApiAuth,
  payload: CompleteOnboardingRequest,
): Promise<CompleteOnboardingResponse> {
  return vitaliaFetch<CompleteOnboardingResponse>(
    `${WIZARD_BASE}/drafts/${encodeURIComponent(payload.draftId)}/complete`,
    {
      method: "POST",
      token: auth.token,
      tenantId: auth.tenantId,
      body: JSON.stringify(payload),
    },
  );
}

/**
 * Build the SSE stream URL for a given draft.
 * The EventSource itself is managed in use-wizard-sse-stream.ts.
 * GET /api/v1/vitalia/wizard/drafts/{draftId}/stream
 *
 * NOTE: SSE requires the token to be passed as a query param because
 * EventSource does not support custom headers. The backend accepts
 * ?token=... for SSE endpoints only (per arch decision T-onboarding-3).
 */
export function buildStreamUrl(draftId: string, token: string): string {
  const params = new URLSearchParams({ token });
  return `${WIZARD_BASE}/drafts/${encodeURIComponent(draftId)}/stream?${params.toString()}`;
}
