// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * MedicalDisclaimerBanner — contextual HIPAA-lite reminder banner.
 *
 * Vitalia-specific: vertical-specific copy per context (treatment/offer/default).
 * Justification: spec § 6.3.7 anti-duplication.
 *
 * Server-compatible: no "use client" needed (no state, no effects).
 *
 * @architecture-group vitalia-ui-strings
 */

import { cn } from "@/lib/cn";
import { MICROCOPY_DISCLAIMER } from "@/features/vitalia/config/microcopy";

export type DisclaimerContext = "default" | "treatment" | "offer";

export interface MedicalDisclaimerBannerProps {
  context?: DisclaimerContext;
  className?: string;
  /** Override default copy when needed */
  customText?: string;
}

export function MedicalDisclaimerBanner({
  context = "default",
  className,
  customText,
}: MedicalDisclaimerBannerProps) {
  const text = customText ?? MICROCOPY_DISCLAIMER[context];

  return (
    <aside
      role="note"
      aria-label="Aviso médico"
      className={cn(
        "flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3",
        className,
      )}
    >
      <span
        className="text-amber-500 text-lg leading-none mt-0.5 flex-shrink-0"
        aria-hidden="true"
      >
        ⚕️
      </span>
      <p className="text-sm text-amber-800 leading-relaxed">{text}</p>
    </aside>
  );
}
