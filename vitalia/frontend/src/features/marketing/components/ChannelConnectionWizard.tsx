// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * ChannelConnectionWizard — 3-step OAuth connection wizard.
 * Step 1: Provider selector
 * Step 2: OAuth redirect (full page navigation — NEVER popup per security rule)
 * Step 3: Confirm + test sync
 *
 * Security invariants:
 * - OAuth: window.location.href = authorizationUrl (full page nav, NOT window.open popup)
 * - External links: target=_blank rel="noopener noreferrer"
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { forwardRef, useState } from "react";
import { cn } from "@/lib/cn";
import { useSyncChannel } from "../api/use-sync-channel";
import { MARKETING_COPY } from "../copy";
import type { ProviderSlug } from "../types/channel";

export type ChannelConnectionWizardProps = {
  open: boolean;
  onClose: () => void;
  onSuccess: (provider: ProviderSlug) => void;
  className?: string;
  /** Test-only: inject authorization URL to skip actual OAuth fetch */
  _testAuthorizationUrl?: string;
};

type WizardStep = 1 | 2 | 3;

const PROVIDERS: Array<{
  slug: ProviderSlug;
  name: string;
  description: string;
}> = [
  {
    slug: "meta_ads",
    name: MARKETING_COPY.channels.providers.meta_ads,
    description: "Conecta tus campañas de Facebook e Instagram Ads",
  },
  {
    slug: "google_ads",
    name: MARKETING_COPY.channels.providers.google_ads,
    description: "Conecta tus campañas de Google Search y Display",
  },
];

/**
 * ChannelConnectionWizard — modal-style OAuth connection flow.
 * NOT rendered when open=false.
 */
export const ChannelConnectionWizard = forwardRef<
  HTMLDivElement,
  ChannelConnectionWizardProps
>(({ open, onClose, onSuccess, className, _testAuthorizationUrl }, ref) => {
  const [step, setStep] = useState<WizardStep>(1);
  const [selectedProvider, setSelectedProvider] = useState<ProviderSlug | null>(
    null,
  );
  const { mutate: syncChannel, isPending: isSyncing } = useSyncChannel();

  if (!open) return null;

  const handleAuthorize = () => {
    if (!selectedProvider) return;

    // Use injected test URL or construct OAuth URL
    const authUrl =
      _testAuthorizationUrl ??
      `/api/v1/vitalia/marketing/channels/${encodeURIComponent(selectedProvider)}/oauth-connect`;

    // SECURITY: Full page navigation — NEVER window.open() popup
    window.location.href = authUrl;
  };

  const handleConfirmSync = () => {
    if (!selectedProvider) return;
    syncChannel(
      { provider: selectedProvider },
      {
        onSuccess: () => {
          setStep(3);
          onSuccess(selectedProvider);
        },
      },
    );
  };

  const handleClose = () => {
    // Reset state before closing
    setStep(1);
    setSelectedProvider(null);
    onClose();
  };

  return (
    <div
      ref={ref}
      role="dialog"
      aria-modal="true"
      aria-label={MARKETING_COPY.connectionWizard.title}
      className={cn(
        "fixed inset-0 z-50 flex items-center justify-center",
        "bg-black/40 backdrop-blur-sm",
        className,
      )}
      onClick={(e) => {
        // Close on backdrop click
        if (e.target === e.currentTarget) handleClose();
      }}
    >
      <div className="relative w-full max-w-md mx-4 rounded-xl vt-bg-surface border vt-border shadow-2xl">
        {/* Step indicator */}
        <div className="flex items-center gap-2 px-5 pt-5">
          {([1, 2, 3] as WizardStep[]).map((s) => (
            <div key={s} className="flex items-center gap-1.5">
              <span
                data-testid={`step-indicator-${s}`}
                aria-current={step === s ? "step" : undefined}
                className={cn(
                  "h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold",
                  step === s
                    ? "vt-bg-primary vt-text-on-primary"
                    : step > s
                      ? "vt-bg-success/20 vt-text-success"
                      : "vt-bg-surface-alt vt-text-muted",
                )}
              >
                {step > s ? "✓" : s}
              </span>
              {s < 3 && (
                <div
                  className={cn(
                    "h-px w-6 vt-bg-surface-alt",
                    step > s && "vt-bg-success/30",
                  )}
                />
              )}
            </div>
          ))}
        </div>

        {/* Header */}
        <div className="px-5 pt-3 pb-1">
          <h2 className="text-base font-semibold vt-text">
            {MARKETING_COPY.connectionWizard.title}
          </h2>
          <p className="text-xs vt-text-muted mt-0.5">
            {MARKETING_COPY.connectionWizard.subtitle}
          </p>
        </div>

        {/* Body */}
        <div className="px-5 py-4">
          {/* Step 1: Provider selector */}
          {step === 1 && (
            <div data-testid="wizard-step-1" className="flex flex-col gap-2">
              {PROVIDERS.map(({ slug, name, description }) => (
                <button
                  key={slug}
                  data-testid={`provider-option-${slug}`}
                  onClick={() => setSelectedProvider(slug)}
                  aria-pressed={selectedProvider === slug}
                  className={cn(
                    "w-full rounded-lg border p-3 text-left transition-colors",
                    "hover:vt-bg-surface-alt",
                    selectedProvider === slug
                      ? "border-current vt-text-primary vt-bg-surface-alt"
                      : "vt-border vt-text",
                  )}
                >
                  <div className="text-sm font-medium">{name}</div>
                  <div className="text-xs vt-text-muted mt-0.5">
                    {description}
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Step 2: OAuth info (this step is typically bypassed by redirect) */}
          {step === 2 && (
            <div data-testid="wizard-step-2" className="flex flex-col gap-3">
              <p className="text-sm vt-text">
                Se abrirá la pantalla de autorización de{" "}
                {selectedProvider
                  ? MARKETING_COPY.channels.providers[selectedProvider]
                  : "tu canal"}
                . Después de autorizar, regresarás aquí automáticamente.
              </p>
            </div>
          )}

          {/* Step 3: Success */}
          {step === 3 && (
            <div
              data-testid="wizard-step-3"
              className="flex flex-col gap-3 items-center py-4"
            >
              <div className="text-2xl" aria-hidden="true">
                ✓
              </div>
              <p className="text-sm font-medium vt-text text-center">
                {MARKETING_COPY.connectionWizard.successTitle}
              </p>
              <p className="text-xs vt-text-muted text-center">
                {MARKETING_COPY.connectionWizard.successMessage}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 border-t vt-border-soft px-5 py-3">
          {step < 3 && (
            <button
              data-testid="wizard-cancel-btn"
              onClick={handleClose}
              className="rounded-md px-3 py-1.5 text-sm vt-text-muted hover:vt-text transition-colors"
            >
              {MARKETING_COPY.connectionWizard.cancelButton}
            </button>
          )}

          {step === 1 && (
            <button
              data-testid="wizard-authorize-btn"
              onClick={handleAuthorize}
              disabled={!selectedProvider}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                "vt-bg-primary vt-text-on-primary hover:opacity-90",
                "disabled:opacity-40 disabled:cursor-not-allowed",
              )}
            >
              {MARKETING_COPY.connectionWizard.authorizeButton}
            </button>
          )}

          {step === 2 && (
            <button
              data-testid="wizard-sync-btn"
              onClick={handleConfirmSync}
              disabled={isSyncing}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                "vt-bg-primary vt-text-on-primary hover:opacity-90",
                "disabled:opacity-40 disabled:cursor-not-allowed",
              )}
            >
              {isSyncing
                ? MARKETING_COPY.channels.syncingLabel
                : "Verificar conexión"}
            </button>
          )}

          {step === 3 && (
            <button
              data-testid="wizard-done-btn"
              onClick={handleClose}
              className="rounded-md px-3 py-1.5 text-sm font-medium vt-bg-primary vt-text-on-primary hover:opacity-90 transition-colors"
            >
              {MARKETING_COPY.ui.confirm}
            </button>
          )}
        </div>
      </div>
    </div>
  );
});
ChannelConnectionWizard.displayName = "ChannelConnectionWizard";
