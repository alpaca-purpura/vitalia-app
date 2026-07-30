// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * LiveLandingSnippetPreview — right panel preview of the clinic's landing page hero.
 *
 * Visual reference: wizard-brand-studio.html (mockup v1 Batch 7)
 * Landing snippet:
 *   - bg-cyan/0.1 gradient → white
 *   - Logo box (grad-mariposa), clinic name, tagline, CTA button
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { WIZARD_COPY } from "../config/copy";
import type { SimulateVoiceResponse } from "../types/wizard-onboarding.types";

export interface LiveLandingSnippetPreviewProps {
  /** Simulation result (contains landingSnippet) */
  data: SimulateVoiceResponse | null;
  /** Whether simulation is loading */
  isLoading?: boolean;
  /** Additional CSS classes */
  className?: string;
}

function ClinicLogoPlaceholder({ name }: { name: string }) {
  const initial = name.charAt(0).toUpperCase() || "V";
  return (
    <div
      className={cn(
        "w-10 h-10 rounded-xl flex items-center justify-center",
        "bg-gradient-to-br from-purple-600 to-blue-700",
        "text-white text-base font-bold select-none shadow-sm",
      )}
      aria-hidden="true"
    >
      {initial}
    </div>
  );
}

ClinicLogoPlaceholder.displayName = "ClinicLogoPlaceholder";

function SkeletonLine({ width = "w-full" }: { width?: string }) {
  return (
    <div
      className={cn("h-3 rounded bg-gray-200 animate-pulse", width)}
      aria-hidden="true"
    />
  );
}

SkeletonLine.displayName = "SkeletonLine";

/**
 * Landing hero snippet card — shows how the clinic branding looks on their site.
 */
export function LiveLandingSnippetPreview({
  data,
  isLoading = false,
  className,
}: LiveLandingSnippetPreviewProps) {
  const copy = WIZARD_COPY.livePreview;
  const snippet = data?.landingSnippet ?? null;

  return (
    <div
      className={cn(
        "rounded-xl border border-gray-200 overflow-hidden shadow-sm",
        className,
      )}
      role="region"
      aria-label={copy.landingTitle}
      aria-busy={isLoading}
    >
      {/* Card header */}
      <div className="px-4 py-3 border-b bg-gray-50">
        <p className="text-sm font-semibold text-gray-800">
          {copy.landingTitle}
        </p>
      </div>

      {/* Landing hero preview */}
      <div className="p-4 bg-gradient-to-br from-cyan-50 to-white">
        {isLoading ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div
                className="w-10 h-10 rounded-xl bg-gray-200 animate-pulse"
                aria-hidden="true"
              />
              <SkeletonLine width="w-32" />
            </div>
            <SkeletonLine />
            <SkeletonLine width="w-4/5" />
            <div
              className="h-8 w-32 rounded-full bg-gray-200 animate-pulse mt-2"
              aria-hidden="true"
            />
          </div>
        ) : snippet ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <ClinicLogoPlaceholder name={snippet.clinicName} />
              <div>
                <p className="text-sm font-bold text-gray-900 leading-tight">
                  {snippet.clinicName}
                </p>
                {snippet.specialty && (
                  <p className="text-xs text-gray-500">{snippet.specialty}</p>
                )}
              </div>
            </div>

            <p className="text-sm text-gray-700 leading-snug">
              {snippet.tagline}
            </p>

            <button
              type="button"
              disabled
              className={cn(
                "rounded-full px-4 py-2 text-sm font-medium",
                "bg-blue-700 text-white",
                "cursor-default opacity-90",
              )}
              aria-label={`Botón de llamada a la acción: ${snippet.ctaText}`}
              tabIndex={-1}
            >
              {snippet.ctaText || copy.landingCtaDefault}
            </button>
          </div>
        ) : (
          <p className="text-xs text-gray-400 italic text-center py-4">
            {copy.emptyState}
          </p>
        )}
      </div>
    </div>
  );
}

LiveLandingSnippetPreview.displayName = "LiveLandingSnippetPreview";
