// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
/**
 * wizard-onboarding.types.ts — TypeScript DTOs mirroring BE Pydantic models
 *
 * camelCase mirror of snake_case Pydantic DTOs.
 * ISO 8601 datetimes as `string`.
 * Matches: vitalia/backend/src/modules/vitalia/copilot/api/routes/wizard_onboarding_routes.py
 *
 * downstream-regression-na: brand-local FE types; no cross-brand consumers
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

/** Wizard operating mode */
export type WizardMode = "libre" | "guiado";

/** Step identifier within the wizard flow */
export type WizardStep =
  | "greet"
  | "extract"
  | "confirm"
  | "simulate"
  | "complete";

/** Slot status */
export type SlotStatus = "confirmed" | "pending" | "optional" | "rejected";

/** Draft status lifecycle */
export type DraftStatus = "in_progress" | "completed" | "expired" | "abandoned";

/** Input extraction source */
export type SlotSource =
  | "user_text"
  | "user_correction"
  | "extracted_url"
  | "extracted_doc";

// ---------------------------------------------------------------------------
// Slot shape (mirrors WizardSlot from copilot/domain/entities/)
// ---------------------------------------------------------------------------

export interface WizardSlot {
  /** Slot identifier (e.g. "clinic_name", "primary_specialty", "tagline") */
  slotId: string;
  /** Human-readable label in Spanish neutro */
  label: string;
  /** Confirmed value (null if pending) */
  value: string | null;
  /** Slot status */
  status: SlotStatus;
  /** Source of the value */
  source: SlotSource | null;
  /** Confidence score 0..1 (null if user-entered) */
  confidence: number | null;
  /** Whether this slot is required to complete onboarding */
  required: boolean;
}

// ---------------------------------------------------------------------------
// Draft (mirrors vitalia_brand_studio_drafts table + OnboardingDraft entity)
// ---------------------------------------------------------------------------

export interface WizardDraft {
  /** Draft UUID */
  id: string;
  /** Tenant UUID (from Clerk org) */
  tenantId: string;
  /** User UUID */
  userId: string;
  /** Draft kind — always "wizard_onboarding" for this feature */
  draftKind: string;
  /** Partial voice/brand profile being constructed */
  voiceProfilePartialJson: Record<string, unknown> | null;
  /** Draft payload (slots + mode + step) */
  draftPayload: {
    mode: WizardMode;
    currentStep: WizardStep;
    slots: WizardSlot[];
    attachmentCount: number;
  } | null;
  /** ISO 8601 — when draft was committed to brand studio (null = in progress) */
  committedAt: string | null;
  /** ISO 8601 — draft expires after N days */
  expiresAt: string | null;
  /** ISO 8601 */
  createdAt: string;
  /** ISO 8601 */
  updatedAt: string;
}

// ---------------------------------------------------------------------------
// Onboarding progress (mirrors vitalia_onboarding_progress table)
// ---------------------------------------------------------------------------

export interface OnboardingProgress {
  /** Progress record UUID */
  id: string;
  tenantId: string;
  userId: string;
  /** Current wizard step */
  step: WizardStep;
  /** Confirmed slots keyed by slotId */
  slotsConfirmed: Record<string, string>;
  /** Pending slot IDs */
  slotsPending: string[];
  /** Wizard mode */
  mode: WizardMode | null;
  /** Current draft ID */
  draftId: string | null;
  /** Attachment metadata */
  attachments: Array<{
    type: "url" | "document" | "audio";
    value: string;
    uploadedAt: string;
  }>;
  /** Status */
  status: DraftStatus;
  /** ISO 8601 */
  completedAt: string | null;
  /** ISO 8601 */
  createdAt: string;
  /** ISO 8601 */
  updatedAt: string;
}

// ---------------------------------------------------------------------------
// API Request/Response shapes
// ---------------------------------------------------------------------------

/** POST /api/v1/vitalia/wizard/drafts — start new draft */
export interface StartDraftRequest {
  mode: WizardMode;
}

export interface StartDraftResponse {
  draftId: string;
  sessionId: string;
  step: WizardStep;
  message: string;
  slots: WizardSlot[];
}

/** POST /api/v1/vitalia/wizard/drafts/{draftId}/extract — extract from URL/doc */
export interface ExtractContextRequest {
  url?: string;
  textContent?: string;
  docUploadId?: string;
}

export interface ExtractContextResponse {
  extractedSlots: WizardSlot[];
  summary: string;
  confidence: number;
  nextStep: WizardStep;
  assistantMessage: string;
}

/** POST /api/v1/vitalia/wizard/drafts/{draftId}/slots/{slotId}/confirm — confirm a slot */
export interface ConfirmSlotRequest {
  slotId: string;
  value: string;
  source: SlotSource;
}

export interface ConfirmSlotResponse {
  slot: WizardSlot;
  allSlotsConfirmed: boolean;
  nextSlotId: string | null;
  assistantMessage: string;
}

/** POST /api/v1/vitalia/wizard/drafts/{draftId}/simulate — simulate voice preview */
export interface SimulateVoiceRequest {
  profilePartial: Record<string, unknown>;
  scenario: "whatsapp_greeting" | "follow_up" | "objection_handling";
}

export interface SimulateVoiceResponse {
  sampleText: string;
  agentName: string;
  scenario: string;
  fromCache: boolean;
  landingSnippet: {
    clinicName: string;
    tagline: string;
    ctaText: string;
    specialty: string;
  } | null;
}

/** POST /api/v1/vitalia/wizard/drafts/{draftId}/complete — finalize onboarding */
export interface CompleteOnboardingRequest {
  draftId: string;
}

export interface CompleteOnboardingResponse {
  tenantId: string;
  isOnboarded: boolean;
  brandStudioDraftId: string;
  completedAt: string;
  message: string;
}

/** GET /api/v1/vitalia/wizard/drafts/{draftId} — get draft state */
export interface GetDraftResponse {
  draft: WizardDraft;
  progress: OnboardingProgress;
  slots: WizardSlot[];
  currentStep: WizardStep;
  canResume: boolean;
}

// ---------------------------------------------------------------------------
// SSE Stream event shapes (EventSource messages)
// ---------------------------------------------------------------------------

/** SSE event from GET /api/v1/vitalia/wizard/drafts/{draftId}/stream */
export type WizardSSEEvent =
  | { type: "token"; content: string }
  | { type: "slot_extracted"; slot: WizardSlot }
  | { type: "step_transition"; nextStep: WizardStep }
  | { type: "typing_start" }
  | { type: "typing_end" }
  | { type: "error"; message: string }
  | { type: "done" };

// ---------------------------------------------------------------------------
// Component-layer state (NOT serialized to API)
// ---------------------------------------------------------------------------

/** Chat message displayed in the thread */
export interface WizardChatMessage {
  /** Stable unique ID — use crypto.randomUUID() or server-provided ID */
  id: string;
  role: "assistant" | "user";
  content: string;
  /** ISO 8601 timestamp */
  timestamp: string;
  /** Optional slot reference for confirmation inline */
  slotRef?: WizardSlot;
  /** If true, shows slot confirm UI inline */
  requiresSlotConfirm?: boolean;
}

/** URL state for the wizard page (mirrors onboardingParsers in 03-arch-fe.md) */
export interface WizardUrlState {
  step: WizardStep;
  mode: WizardMode | null;
  draftId: string | null;
}

/** Live preview state */
export interface LivePreviewState {
  isLoading: boolean;
  whatsApp: SimulateVoiceResponse | null;
  lastUpdatedAt: string | null;
}
