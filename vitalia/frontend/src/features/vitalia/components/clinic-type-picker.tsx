// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * ClinicTypePicker — medical-vertical clinic type selector.
 *
 * Vitalia-specific: dental/psychology/psychiatry/wellness with suitability hints.
 * No generic equivalent in @luana/ui (other brands have their own pickers).
 * Justification: spec § 6.3.1 anti-duplication.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { cn } from "@/lib/cn";
import { MICROCOPY_ONBOARDING } from "@/features/vitalia/config/microcopy";
import type { ClinicType } from "@/features/vitalia/types/vitalia.types";

export interface ClinicTypePickerProps {
  value: ClinicType | null;
  onChange: (value: ClinicType) => void;
  disabled?: boolean;
}

const CLINIC_OPTIONS: { value: ClinicType; icon: string; ariaLabel: string }[] =
  [
    { value: "dental", icon: "🦷", ariaLabel: "Dental" },
    { value: "psychology", icon: "🧠", ariaLabel: "Psicología" },
    { value: "psychiatry", icon: "💊", ariaLabel: "Psiquiatría" },
    { value: "wellness", icon: "✨", ariaLabel: "Wellness" },
  ];

export function ClinicTypePicker({
  value,
  onChange,
  disabled = false,
}: ClinicTypePickerProps) {
  return (
    <fieldset
      className="border-0 p-0 m-0"
      aria-label={MICROCOPY_ONBOARDING.fields.clinicType}
      disabled={disabled}
    >
      <legend className="text-sm font-medium text-gray-700 mb-3">
        {MICROCOPY_ONBOARDING.fields.clinicType}
      </legend>
      <div
        className="grid grid-cols-2 gap-3"
        role="radiogroup"
        aria-label={MICROCOPY_ONBOARDING.fields.clinicType}
      >
        {CLINIC_OPTIONS.map((option) => {
          const microcopy = MICROCOPY_ONBOARDING.clinicTypes[option.value];
          const isSelected = value === option.value;
          return (
            <label
              key={option.value}
              className={cn(
                "relative flex flex-col gap-1 p-4 rounded-lg border-2 cursor-pointer transition-all",
                "hover:border-blue-400 hover:bg-blue-50",
                isSelected
                  ? "border-blue-600 bg-blue-50"
                  : "border-gray-200 bg-white",
                disabled && "opacity-50 cursor-not-allowed pointer-events-none",
              )}
            >
              <input
                type="radio"
                name="clinic-type"
                value={option.value}
                checked={isSelected}
                onChange={() => onChange(option.value)}
                disabled={disabled}
                aria-label={option.ariaLabel}
                className="sr-only"
              />
              <span className="text-2xl" aria-hidden="true">
                {option.icon}
              </span>
              <span className="font-semibold text-gray-900 text-sm">
                {microcopy.label}
              </span>
              <span className="text-xs text-gray-500">{microcopy.hint}</span>
              {isSelected && (
                <span
                  className="absolute top-2 right-2 w-4 h-4 rounded-full bg-blue-600 flex items-center justify-center"
                  aria-hidden="true"
                >
                  <span className="w-2 h-2 rounded-full bg-white" />
                </span>
              )}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
