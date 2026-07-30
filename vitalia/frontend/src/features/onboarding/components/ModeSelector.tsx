// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * ModeSelector — input mode selection (URL / Document / Audio).
 *
 * Visual reference: wizard-brand-studio.html (mockup v1 Batch 7)
 * - URL mode: Globe icon, enabled
 * - Document mode: FileText icon, enabled
 * - Audio mode: Mic icon, DISABLED (Slice 2 per OQ-3 ratification 2026-05-18)
 *   shows tooltip "Disponible próximamente"
 *
 * Per 03-arch-fe.md § ratification OQ-3:
 *   "Audio DISABLED (Slice 2). ModeSelector shows 3 buttons but audio is
 *    disabled+tooltip 'Disponible próximamente'."
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useState } from "react";
import { cn } from "@/lib/cn";
import { WIZARD_COPY } from "../config/copy";

export type InputMode = "url" | "document" | "audio";

export interface ModeSelectorProps {
  /** Currently selected mode */
  selectedMode: InputMode;
  /** Called when user selects a mode (audio is disabled — will not be called for audio) */
  onModeChange: (mode: InputMode) => void;
  /** Additional CSS classes */
  className?: string;
}

interface ModeOption {
  id: InputMode;
  label: string;
  description: string;
  disabled: boolean;
  disabledTooltip?: string;
  icon: React.ReactNode;
}

function GlobeIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  );
}

function FileTextIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14,2 14,8 20,8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10,9 9,9 8,9" />
    </svg>
  );
}

function MicIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  );
}

/**
 * Mode selector buttons for URL / Document / Audio input.
 * Audio is disabled pending Slice 2.
 */
export function ModeSelector({
  selectedMode,
  onModeChange,
  className,
}: ModeSelectorProps) {
  const [hoveredTooltip, setHoveredTooltip] = useState<InputMode | null>(null);
  const copy = WIZARD_COPY.modeSelector;

  const options: ModeOption[] = [
    {
      id: "url",
      label: copy.options.url.label,
      description: copy.options.url.description,
      disabled: false,
      icon: <GlobeIcon />,
    },
    {
      id: "document",
      label: copy.options.document.label,
      description: copy.options.document.description,
      disabled: false,
      icon: <FileTextIcon />,
    },
    {
      id: "audio",
      label: copy.options.audio.label,
      description: copy.options.audio.description,
      disabled: true,
      disabledTooltip: copy.options.audio.disabledTooltip,
      icon: <MicIcon />,
    },
  ];

  return (
    <div
      className={cn("space-y-3", className)}
      role="group"
      aria-label={copy.label}
    >
      <p className="text-sm font-medium text-gray-700">{copy.label}</p>
      <div className="flex flex-col gap-2">
        {options.map((option) => {
          const isSelected = selectedMode === option.id;
          return (
            <div key={option.id} className="relative">
              <button
                type="button"
                onClick={() => {
                  if (!option.disabled) onModeChange(option.id);
                }}
                disabled={option.disabled}
                aria-pressed={isSelected}
                aria-describedby={
                  option.disabled ? `${option.id}-tooltip` : undefined
                }
                onMouseEnter={() => {
                  if (option.disabled) setHoveredTooltip(option.id);
                }}
                onMouseLeave={() => setHoveredTooltip(null)}
                onFocus={() => {
                  if (option.disabled) setHoveredTooltip(option.id);
                }}
                onBlur={() => setHoveredTooltip(null)}
                className={cn(
                  "w-full flex items-start gap-3 rounded-lg border p-3 text-left",
                  "transition-colors duration-150",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600",
                  isSelected
                    ? "border-blue-700 bg-blue-50 text-blue-900"
                    : "border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50",
                  option.disabled &&
                    "opacity-50 cursor-not-allowed hover:bg-white hover:border-gray-200",
                )}
              >
                <span
                  className={cn(
                    "flex-shrink-0 mt-0.5",
                    isSelected ? "text-blue-700" : "text-gray-400",
                  )}
                >
                  {option.icon}
                </span>
                <span className="flex-1 min-w-0">
                  <span className="block text-sm font-medium">
                    {option.label}
                  </span>
                  <span className="block text-xs text-gray-500 mt-0.5">
                    {option.description}
                  </span>
                </span>
                {isSelected && !option.disabled && (
                  <span
                    className="flex-shrink-0 w-4 h-4 mt-0.5 rounded-full border-2 border-blue-700 bg-blue-700 flex items-center justify-center"
                    aria-hidden="true"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-white" />
                  </span>
                )}
              </button>

              {/* Tooltip for disabled audio */}
              {option.disabled && option.disabledTooltip && (
                <span
                  id={`${option.id}-tooltip`}
                  role="tooltip"
                  className={cn(
                    "absolute left-1/2 -translate-x-1/2 -bottom-7 z-10",
                    "bg-gray-800 text-white text-xs rounded px-2 py-1 whitespace-nowrap",
                    "pointer-events-none transition-opacity duration-150",
                    hoveredTooltip === option.id ? "opacity-100" : "opacity-0",
                  )}
                >
                  {option.disabledTooltip}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

ModeSelector.displayName = "ModeSelector";
