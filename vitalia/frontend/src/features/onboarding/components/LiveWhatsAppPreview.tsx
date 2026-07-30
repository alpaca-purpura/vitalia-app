// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * LiveWhatsAppPreview — right panel preview of how the agent writes on WhatsApp.
 *
 * Visual reference: wizard-brand-studio.html (mockup v1 Batch 7)
 * WhatsApp card:
 *   - bg-white rounded-lg shadow-sm border
 *   - Header: "Cómo escribe Adrián", success indicator
 *   - Body: bg-gray/0.4, agent message box with gradient avatar
 *   - Footer: cost indicator + model name
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { WIZARD_COPY } from "../config/copy";
import type { SimulateVoiceResponse } from "../types/wizard-onboarding.types";

export interface LiveWhatsAppPreviewProps {
  /** Simulation result (null = empty state or loading) */
  data: SimulateVoiceResponse | null;
  /** Whether simulation is loading */
  isLoading?: boolean;
  /** Additional CSS classes */
  className?: string;
}

function AdrianAvatar() {
  return (
    <span
      className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
        "bg-gradient-to-br from-teal-500 to-cyan-600",
        "text-white text-xs font-bold select-none",
      )}
      aria-hidden="true"
    >
      A
    </span>
  );
}

AdrianAvatar.displayName = "AdrianAvatar";

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
 * WhatsApp agent message preview card.
 */
export function LiveWhatsAppPreview({
  data,
  isLoading = false,
  className,
}: LiveWhatsAppPreviewProps) {
  const copy = WIZARD_COPY.livePreview;

  return (
    <div
      className={cn(
        "rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden",
        className,
      )}
      role="region"
      aria-label={copy.whatsAppTitle}
      aria-busy={isLoading}
    >
      {/* Card header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
        <div>
          <p className="text-sm font-semibold text-gray-800">
            {copy.whatsAppTitle}
          </p>
          <p className="text-xs text-gray-500">{copy.whatsAppSubtitle}</p>
        </div>
        {data && (
          <span
            className="flex items-center gap-1 text-xs text-green-600 font-medium"
            aria-label="Vista previa generada"
          >
            <span
              className="w-1.5 h-1.5 rounded-full bg-green-500"
              aria-hidden="true"
            />
            Listo
          </span>
        )}
      </div>

      {/* Card body */}
      <div className="p-4 bg-gray-50/50">
        {isLoading ? (
          <div className="space-y-2">
            <SkeletonLine />
            <SkeletonLine width="w-4/5" />
            <SkeletonLine width="w-3/5" />
          </div>
        ) : data ? (
          <div className="flex items-start gap-3">
            <AdrianAvatar />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-gray-700 mb-1">
                {data.agentName}
              </p>
              <div className="rounded-xl rounded-tl-sm bg-white border border-gray-200 px-3 py-2 shadow-xs">
                <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                  {data.sampleText}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-xs text-gray-400 italic text-center py-4">
            {copy.emptyState}
          </p>
        )}
      </div>

      {/* Card footer */}
      {data && (
        <div className="flex items-center justify-end gap-3 px-4 py-2 border-t bg-gray-50">
          <span className="text-[10px] text-gray-400">
            {copy.modelLabel}: {data.scenario}
          </span>
          {data.fromCache && (
            <span className="text-[10px] text-gray-400">(desde caché)</span>
          )}
        </div>
      )}
    </div>
  );
}

LiveWhatsAppPreview.displayName = "LiveWhatsAppPreview";
