// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * marca-voice-api.ts — API client for Voz y tono sub-sub-tab (T-6).
 *
 * Endpoints:
 *   GET  /api/v1/lisa/marca/personality         — fetch personality + voice blocks
 *   PATCH /api/v1/lisa/marca/personality        — update archetype + 6 voice blocks
 *   POST /api/v1/lisa/marca/voice-preview       — server-side compile BRAND_VOICE slot
 *   GET  /api/v1/lisa/marca/prohibited-phrases  — fetch tenant + seed phrases
 *   POST /api/v1/lisa/marca/voice-warning-override — audit log voice override
 *
 * Auth: fetchClient auto-injects X-Tenant-ID (HIPAA-lite).
 * React Query keys: marcaKeys factory extended with personality + voicePreview + blocklist.
 *
 * Anti-creep (sales-agent-brand-voice.md): NO health_voice_validator. Soft warning only.
 * Voice compiler v2 LIBRARY-ONLY on BE — no LLM dispatch in FE.
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 03-arch.md § 4.2 + 06-tickets.yaml T-6 deliverables
 * downstream-regression-na: brand-local vitalia FE API; no cross-brand consumers
 */

import { fetchClient } from "@/lib/api/fetchClient";
import type { SaludArchetype } from "../types/marca/personality-schema";

// ── API opts (shared pattern from marca.ts T-5) ───────────────────────────────

interface ApiOpts {
  token: string;
  tenantId: string;
  clinicId?: string | null;
  /** Clerk user ID — sent as X-User-ID header for mutation audit log. */
  userId?: string | null;
  /** Vitalia role — sent as X-User-Role header for RBAC guard on mutations. */
  userRole?: string | null;
}

// ── Response types (camelCase mirrors of Pydantic DTOs, ISO 8601 datetimes as string) ──

export interface PersonalityResponse {
  tenantId: string;
  personalityProfileId: string;
  archetype: SaludArchetype;
  soISpeak: string;
  soIDontSpeak: string;
  technicalContext: string;
  formatInstructions: string;
  identityAnchor: string;
  domainContext: string;
  compiledAt: string | null; // ISO 8601
  compilerVersion: string;
  updatedAt?: string; // ISO 8601
}

export interface PersonalityPatchPayload {
  archetype?: SaludArchetype;
  soISpeak?: string;
  soIDontSpeak?: string;
  technicalContext?: string;
  formatInstructions?: string;
  identityAnchor?: string;
  domainContext?: string;
}

export interface ProhibitedPhraseItem {
  id: string;
  phrase: string;
  suggestedAlternative: string;
  severity: "low" | "medium" | "high";
  countryScope: string | null;
  isSeed: boolean;
}

export interface ProhibitedPhrasesListResponse {
  items: ProhibitedPhraseItem[];
  total: number;
}

export interface VoicePreviewResponse {
  personalityProfileId: string;
  sampleWhatsapp: string;
  sampleEmailReactivacion: string;
  compiledAt: string; // ISO 8601
  compilerVersion: string;
  cacheHit: boolean;
}

export interface VoiceWarningOverridePayload {
  phraseId: string;
  section: "so_i_speak" | "so_i_dont_speak";
  userTextExcerpt: string;
}

// ── Personality endpoints ──────────────────────────────────────────────────────

export async function getPersonality(opts: ApiOpts): Promise<PersonalityResponse> {
  return fetchClient<PersonalityResponse>("/api/v1/lisa/marca/personality", opts);
}

export async function updatePersonality(
  opts: ApiOpts,
  payload: PersonalityPatchPayload,
): Promise<PersonalityResponse> {
  // Build mutation-specific headers: X-User-ID + X-User-Role required by
  // require_brand_owner_access() RBAC guard on PATCH /personality.
  //
  // X-User-ID = the REAL Clerk userId of the authenticated owner. The BE
  // (story estabilizar-harness-e2e-lisa-marca, T-3 #2b) resolves the audit
  // actor from the JWT clerk_sub → users.id UUID, so the FE just forwards the
  // real Clerk userId — NEVER the tenantId (the tenant as audit actor was the
  // HIPAA-lite "quién" bug, sub-bug #2). No fallback to tenantId: a missing
  // userId means an anonymous mutation, which we refuse rather than mislabel.
  if (!opts.userId) {
    throw new Error(
      "updatePersonality requires an authenticated Clerk userId (X-User-ID audit actor)",
    );
  }

  const mutationHeaders: Record<string, string> = {
    "X-User-ID": opts.userId,
    // Owner role for brand config mutations (no PHI — owner-level endpoint).
    "X-User-Role": opts.userRole ?? "owner",
  };

  return fetchClient<PersonalityResponse>("/api/v1/lisa/marca/personality", {
    ...opts,
    method: "PATCH",
    headers: mutationHeaders,
    body: JSON.stringify(payload),
  });
}

// ── Prohibited phrases endpoint ───────────────────────────────────────────────

export async function getProhibitedPhrases(
  opts: ApiOpts,
): Promise<ProhibitedPhrasesListResponse> {
  return fetchClient<ProhibitedPhrasesListResponse>(
    "/api/v1/lisa/marca/prohibited-phrases",
    opts,
  );
}

// ── Voice warning override (audit log) ───────────────────────────────────────

export async function postVoiceWarningOverride(
  opts: ApiOpts,
  payload: VoiceWarningOverridePayload,
): Promise<void> {
  await fetchClient<void>("/api/v1/lisa/marca/voice-warning-override", {
    ...opts,
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ── Voice preview endpoint ─────────────────────────────────────────────────────

export async function getVoicePreview(
  opts: ApiOpts,
  blocksHash: string,
): Promise<VoicePreviewResponse> {
  return fetchClient<VoicePreviewResponse>(
    `/api/v1/lisa/marca/voice-preview?blocks_hash=${encodeURIComponent(blocksHash)}`,
    opts,
  );
}
