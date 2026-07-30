// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * WizardOnboardingLayout — Main wizard layout with chat-LEFT 50/50 split.
 *
 * Visual reference: wizard-brand-studio.html (mockup v1 Batch 7)
 *
 * Layout structure:
 *   TopBar (h-14):
 *     - Vitalia logo (V badge gradient)
 *     - "Configuración de tu clínica" title
 *     - Slot counter pill
 *     - "Cerrar asistente" button
 *
 *   Main grid (grid-cols-2, full height):
 *     LEFT (chat): SlotTrackerSticky + WizardChatThread + InputComposer
 *     RIGHT (preview): LiveWhatsAppPreview + LiveLandingSnippetPreview
 *
 * Responsive: below md breakpoint, stacks vertically (chat on top, preview below).
 *
 * State orchestration lives here:
 *   - useWizardUrlState: step + mode + draftId from URL
 *   - useWizardOnboardingState: draft data from API
 *   - useWizardSSEStream: live assistant messages
 *   - useWizardSlotExtraction: URL/doc extraction
 *   - useWizardLivePreview: debounced simulation
 *   - useWizardCompletion: finalise onboarding
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth, useOrganization } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/cn";
import { WIZARD_COPY } from "../config/copy";
import { SlotTrackerSticky } from "./SlotTrackerSticky";
import { WizardChatThread } from "./WizardChatThread";
import { LiveWhatsAppPreview } from "./LiveWhatsAppPreview";
import { LiveLandingSnippetPreview } from "./LiveLandingSnippetPreview";
import { CloseSetupWarningModal } from "./CloseSetupWarningModal";
import { WizardCompletionTransition } from "./WizardCompletionTransition";
import { useWizardUrlState } from "../hooks/use-wizard-url-state";
import { useWizardOnboardingState } from "../hooks/use-wizard-onboarding-state";
import { useWizardSSEStream } from "../hooks/use-wizard-sse-stream";
import { useWizardSlotExtraction } from "../hooks/use-wizard-slot-extraction";
import { useWizardLivePreview } from "../hooks/use-wizard-live-preview";
import { useWizardCompletion } from "../hooks/use-wizard-completion";
import { startDraft, confirmSlot } from "../api/wizard-onboarding-api";
import { wizardQueryKeys } from "../hooks/use-wizard-onboarding-state";
import type {
  WizardChatMessage,
  SlotSource,
} from "../types/wizard-onboarding.types";

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function VitaliaLogo() {
  return (
    <div className="flex items-center gap-2" aria-label="Vitalia">
      <span
        className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
          "bg-gradient-to-br from-blue-700 to-purple-600",
          "text-white text-xs font-bold",
        )}
        aria-hidden="true"
      >
        V
      </span>
      <div className="leading-tight">
        <p className="text-sm font-semibold text-gray-900">
          {WIZARD_COPY.topBar.title}
        </p>
        <p className="text-[10px] text-gray-500">
          {WIZARD_COPY.topBar.subtitle}
        </p>
      </div>
    </div>
  );
}

VitaliaLogo.displayName = "VitaliaLogo";

function LoadingState() {
  return (
    <div
      className="flex h-screen items-center justify-center"
      aria-live="polite"
    >
      <div className="text-center space-y-3">
        <div
          className="w-8 h-8 rounded-full border-2 border-blue-700 border-t-transparent animate-spin mx-auto"
          aria-hidden="true"
        />
        <p className="text-sm text-gray-500">
          {WIZARD_COPY.loading.initializingWizard}
        </p>
      </div>
    </div>
  );
}

LoadingState.displayName = "LoadingState";

function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div
      className="flex h-screen items-center justify-center p-6"
      role="alert"
      aria-live="assertive"
    >
      <div className="max-w-sm text-center space-y-4">
        <div
          className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto"
          aria-hidden="true"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-red-600"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
        </div>
        <p className="text-sm text-gray-600 leading-relaxed">{message}</p>
        <button
          type="button"
          onClick={onRetry}
          className="rounded-xl px-4 py-2 text-sm font-medium bg-blue-700 text-white hover:bg-blue-800 transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"
        >
          {WIZARD_COPY.errors.retryButton}
        </button>
      </div>
    </div>
  );
}

ErrorState.displayName = "ErrorState";

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export interface WizardOnboardingLayoutProps {
  /** Additional CSS classes */
  className?: string;
}

/**
 * Main wizard onboarding layout — orchestrates all wizard sub-components.
 * This is the root Client Component for the /onboarding/wizard page.
 */
export function WizardOnboardingLayout({
  className,
}: WizardOnboardingLayoutProps) {
  const router = useRouter();
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const { organization } = useOrganization();
  const queryClient = useQueryClient();

  // URL state
  const { urlState, setUrlState, advanceStep } = useWizardUrlState();
  const { step, draftId } = urlState;

  // Local state
  const [messages, setMessages] = useState<WizardChatMessage[]>([]);
  const [isCloseModalOpen, setIsCloseModalOpen] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [confirmingSlotId, setConfirmingSlotId] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);

  // Draft query
  const { data: draftData, error: draftError } = useWizardOnboardingState({
    draftId,
  });

  // SSE stream
  const [sseToken, setSseToken] = useState<string | null>(null);
  const {
    isStreaming,
    latestMessage,
    error: sseError,
    disconnect: sseDisconnect,
  } = useWizardSSEStream({
    draftId,
    token: sseToken,
    enabled: Boolean(draftId && step !== "complete"),
    onEvent: useCallback(
      (event: import("../types/wizard-onboarding.types").WizardSSEEvent) => {
        if (event.type === "slot_extracted" && event.slot) {
          addSystemMessage({
            role: "assistant",
            content: `Encontré este dato: ${event.slot.label}`,
            slotRef: event.slot,
            requiresSlotConfirm: true,
          });
        }
        if (event.type === "step_transition" && event.nextStep) {
          advanceStep(event.nextStep);
        }
      },
      [advanceStep],
    ),
  });

  // Slot extraction
  const extractionMutation = useWizardSlotExtraction({
    draftId: draftId ?? "",
    onSuccess: (result) => {
      result.extractedSlots.forEach((slot) => {
        addSystemMessage({
          role: "assistant",
          content: result.assistantMessage,
          slotRef: slot,
          requiresSlotConfirm: true,
        });
      });
      if (result.nextStep) advanceStep(result.nextStep);
    },
    onError: () => addErrorMessage(WIZARD_COPY.errors.extractFailed),
  });

  // Live preview
  const slots = draftData?.slots ?? [];
  const profilePartial: Record<string, unknown> = {};
  slots
    .filter((s) => s.status === "confirmed")
    .forEach((s) => {
      if (s.value) profilePartial[s.slotId] = s.value;
    });

  const { data: previewSimData, isLoading: isPreviewLoading } =
    useWizardLivePreview({
      draftId,
      profilePartial:
        Object.keys(profilePartial).length > 0 ? profilePartial : null,
      enabled: Boolean(draftId),
    });

  // Completion
  const completionMutation = useWizardCompletion({
    draftId: draftId ?? "",
    onSuccess: () => {
      setIsCompleted(true);
      sseDisconnect();
    },
    onError: () => addErrorMessage(WIZARD_COPY.errors.completeFailed),
  });

  // Start draft mutation (initializes wizard)
  const startDraftMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      const tenantId = organization?.id;
      if (!tenantId) throw new Error("Organización no disponible");
      setSseToken(token);
      return startDraft({ token, tenantId }, { mode: "guiado" });
    },
    onSuccess: (result) => {
      setUrlState({ draftId: result.draftId, step: result.step });
      addSystemMessage({ role: "assistant", content: result.message });
      setStartError(null);
    },
    onError: () => setStartError(WIZARD_COPY.errors.genericError),
  });

  // Confirm slot mutation
  const confirmSlotMutation = useMutation({
    mutationFn: async (args: {
      slotId: string;
      value: string;
      source: SlotSource;
    }) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      const tenantId = organization?.id;
      if (!tenantId) throw new Error("Organización no disponible");
      if (!draftId) throw new Error("Draft no disponible");
      return confirmSlot({ token, tenantId }, draftId, args);
    },
    onSuccess: (result) => {
      setConfirmingSlotId(null);
      void queryClient.invalidateQueries({
        queryKey: wizardQueryKeys.draft(draftId ?? ""),
      });
      if (result.allSlotsConfirmed) {
        completionMutation.mutate();
      }
      if (result.assistantMessage) {
        addSystemMessage({
          role: "assistant",
          content: result.assistantMessage,
        });
      }
    },
    onError: () => {
      setConfirmingSlotId(null);
      addErrorMessage(WIZARD_COPY.errors.confirmSlotFailed);
    },
  });

  // Stable ref for startDraftMutation.mutate so the init effect below
  // doesn't need to list the mutation object as a dependency (its identity
  // changes every render but the behaviour is stable).
  const startDraftMutateRef = useRef(startDraftMutation.mutate);
  useEffect(() => {
    startDraftMutateRef.current = startDraftMutation.mutate;
  });

  // Initialize wizard on mount (if no draftId in URL).
  // Runs only when auth loads and there's no draft to resume.
  const hasInitializedRef = useRef(false);
  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    if (draftId) return; // Resume from URL
    if (hasInitializedRef.current) return;
    hasInitializedRef.current = true;
    startDraftMutateRef.current();
  }, [isLoaded, isSignedIn, draftId]);

  // Capture SSE token when auth loads
  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    getToken().then((t) => {
      if (t) setSseToken(t);
    });
  }, [isLoaded, isSignedIn, getToken]);

  // Add SSE streaming message to thread when streaming completes
  useEffect(() => {
    if (!isStreaming && latestMessage) {
      addSystemMessage({ role: "assistant", content: latestMessage });
    }
  }, [isStreaming, latestMessage]);

  // Helpers
  const addSystemMessage = useCallback(
    (msg: Omit<WizardChatMessage, "id" | "timestamp">) => {
      setMessages((prev) => [
        ...prev,
        {
          ...msg,
          id: crypto.randomUUID(),
          timestamp: new Date().toLocaleTimeString("es-419", {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    },
    [],
  );

  const addErrorMessage = useCallback(
    (text: string) => {
      addSystemMessage({ role: "assistant", content: text });
    },
    [addSystemMessage],
  );

  // User sends message
  const handleSend = useCallback(
    (text: string) => {
      addSystemMessage({ role: "user", content: text });
      if (extractionMutation.isPending) return;
      // If step is greet or extract, try URL extraction
      if (/^https?:\/\//i.test(text)) {
        extractionMutation.mutate({ url: text });
      } else {
        extractionMutation.mutate({ textContent: text });
      }
    },
    [addSystemMessage, extractionMutation],
  );

  const handleConfirmSlot = useCallback(
    (slotId: string, value: string, source: SlotSource) => {
      setConfirmingSlotId(slotId);
      confirmSlotMutation.mutate({ slotId, value, source });
    },
    [confirmSlotMutation],
  );

  const handleRejectSlot = useCallback(
    (slotId: string) => {
      addSystemMessage({
        role: "assistant",
        content: `Entendido, cuéntame el valor correcto para: ${
          draftData?.slots.find((s) => s.slotId === slotId)?.label ?? slotId
        }`,
      });
    },
    [addSystemMessage, draftData],
  );

  // Loading state
  if (!isLoaded || startDraftMutation.isPending) {
    return <LoadingState />;
  }

  // Error state
  if (startError || draftError || sseError) {
    const errorMsg =
      startError ||
      (draftError instanceof Error ? draftError.message : null) ||
      sseError ||
      WIZARD_COPY.errors.genericError;
    return (
      <ErrorState
        message={errorMsg}
        onRetry={() => {
          setStartError(null);
          startDraftMutation.mutate();
        }}
      />
    );
  }

  const confirmedSlots = slots.filter((s) => s.status === "confirmed").length;
  const totalSlots = slots.filter((s) => s.required).length;
  const progress = totalSlots > 0 ? confirmedSlots / totalSlots : 0;

  return (
    <div
      className={cn(
        "flex flex-col h-screen bg-white overflow-hidden",
        className,
      )}
      role="application"
      aria-label={WIZARD_COPY.a11y.wizardRegionLabel}
    >
      {/* TopBar */}
      <header className="flex items-center justify-between h-14 px-4 border-b bg-white flex-shrink-0">
        <VitaliaLogo />

        <div className="flex items-center gap-3">
          {/* Slot counter */}
          {totalSlots > 0 && (
            <span
              className="text-xs text-gray-500 font-medium hidden sm:block"
              aria-live="polite"
            >
              {WIZARD_COPY.topBar.slotCounterLabel(confirmedSlots, totalSlots)}
            </span>
          )}

          {/* Close button */}
          <button
            type="button"
            onClick={() => setIsCloseModalOpen(true)}
            className={cn(
              "flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-medium",
              "border border-gray-200 text-gray-600",
              "hover:bg-gray-50 transition-colors duration-150",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400",
            )}
            aria-label={WIZARD_COPY.topBar.closeButton}
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
            <span className="hidden sm:inline">
              {WIZARD_COPY.topBar.closeButton}
            </span>
          </button>
        </div>
      </header>

      {/* Main content — 50/50 grid */}
      <main className="flex-1 grid grid-cols-1 md:grid-cols-2 min-h-0 overflow-hidden">
        {/* LEFT — Chat section */}
        <section
          className="flex flex-col min-h-0 border-r border-gray-100"
          aria-label={WIZARD_COPY.a11y.chatRegionLabel}
        >
          {/* Slot tracker */}
          <SlotTrackerSticky slots={slots} />

          {/* Chat thread + input */}
          <WizardChatThread
            messages={messages}
            isTyping={isStreaming || extractionMutation.isPending}
            isSubmitting={
              extractionMutation.isPending || confirmSlotMutation.isPending
            }
            onSend={handleSend}
            onConfirmSlot={handleConfirmSlot}
            onRejectSlot={handleRejectSlot}
            onBack={() => router.back()}
            onSkip={() => completionMutation.mutate()}
            confirmingSlotId={confirmingSlotId}
            modeLabel={urlState.mode ?? undefined}
            progress={progress}
            className="flex-1 min-h-0"
          />
        </section>

        {/* RIGHT — Live preview section */}
        <section
          className="flex flex-col gap-4 p-4 overflow-y-auto bg-gray-50 min-h-0 hidden md:flex"
          aria-label={WIZARD_COPY.a11y.previewRegionLabel}
        >
          <div className="flex-shrink-0 border-b pb-3">
            <p className="text-sm font-semibold text-gray-800">
              {WIZARD_COPY.livePreview.panelTitle}
            </p>
            <p className="text-xs text-gray-500">
              {WIZARD_COPY.livePreview.panelSubtitle}
            </p>
          </div>

          <LiveWhatsAppPreview
            data={previewSimData ?? null}
            isLoading={isPreviewLoading}
          />

          <LiveLandingSnippetPreview
            data={previewSimData ?? null}
            isLoading={isPreviewLoading}
          />
        </section>
      </main>

      {/* Close warning modal */}
      <CloseSetupWarningModal
        isOpen={isCloseModalOpen}
        onConfirmClose={() => {
          setIsCloseModalOpen(false);
          router.push("/");
        }}
        onCancel={() => setIsCloseModalOpen(false)}
      />

      {/* Completion transition */}
      <WizardCompletionTransition
        isActive={isCompleted || step === "complete"}
        onNavigate={() => router.push("/")}
      />
    </div>
  );
}

WizardOnboardingLayout.displayName = "WizardOnboardingLayout";
