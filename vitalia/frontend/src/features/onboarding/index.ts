// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
/**
 * features/onboarding — public API gate.
 *
 * Consumers import from this barrel. Do NOT import directly from sub-paths.
 * Named exports only (no default exports per arch rule FE-A3).
 *
 * downstream-regression-na: brand-local FE feature; no cross-brand consumers
 */

// ─── Components ────────────────────────────────────────────────────────────
export { WizardOnboardingLayout } from "./components/WizardOnboardingLayout";
export type { WizardOnboardingLayoutProps } from "./components/WizardOnboardingLayout";

export { WizardChatThread } from "./components/WizardChatThread";
export type { WizardChatThreadProps } from "./components/WizardChatThread";

export { SlotTrackerSticky } from "./components/SlotTrackerSticky";
export type { SlotTrackerStickyProps } from "./components/SlotTrackerSticky";

export { ModeSelector } from "./components/ModeSelector";
export type { ModeSelectorProps } from "./components/ModeSelector";

export { SlotConfirmInline } from "./components/SlotConfirmInline";
export type { SlotConfirmInlineProps } from "./components/SlotConfirmInline";

export { LiveWhatsAppPreview } from "./components/LiveWhatsAppPreview";
export type { LiveWhatsAppPreviewProps } from "./components/LiveWhatsAppPreview";

export { LiveLandingSnippetPreview } from "./components/LiveLandingSnippetPreview";
export type { LiveLandingSnippetPreviewProps } from "./components/LiveLandingSnippetPreview";

export { CloseSetupWarningModal } from "./components/CloseSetupWarningModal";
export type { CloseSetupWarningModalProps } from "./components/CloseSetupWarningModal";

export { WizardCompletionTransition } from "./components/WizardCompletionTransition";
export type { WizardCompletionTransitionProps } from "./components/WizardCompletionTransition";

// ─── Hooks ──────────────────────────────────────────────────────────────────
export {
  useWizardOnboardingState,
  wizardQueryKeys,
} from "./hooks/use-wizard-onboarding-state";
export { useWizardSlotExtraction } from "./hooks/use-wizard-slot-extraction";
export { useWizardLivePreview } from "./hooks/use-wizard-live-preview";
export { useWizardCompletion } from "./hooks/use-wizard-completion";
export { useWizardSSEStream } from "./hooks/use-wizard-sse-stream";
export type {
  SSEStreamState,
  UseWizardSSEStreamOptions,
} from "./hooks/use-wizard-sse-stream";
export { useWizardUrlState } from "./hooks/use-wizard-url-state";
export type { UseWizardUrlStateReturn } from "./hooks/use-wizard-url-state";

// ─── Types ──────────────────────────────────────────────────────────────────
export type {
  WizardMode,
  WizardStep,
  WizardSlot,
  SlotStatus,
  SlotSource,
  DraftStatus,
  WizardDraft,
  OnboardingProgress,
  WizardChatMessage,
  WizardSSEEvent,
  LivePreviewState,
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
} from "./types/wizard-onboarding.types";

// ─── API ────────────────────────────────────────────────────────────────────
export {
  startDraft,
  getDraft,
  extractContext,
  confirmSlot,
  simulateVoice,
  completeOnboarding,
  buildStreamUrl,
} from "./api/wizard-onboarding-api";
export type { WizardApiAuth } from "./api/wizard-onboarding-api";

// ─── Config ──────────────────────────────────────────────────────────────────
export { WIZARD_COPY } from "./config/copy";
