// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
"use client";
/**
 * WizardCompletionTransition — morph 400ms transition on onboarding completion.
 *
 * Per spec (Batch 1 ratificado):
 *   - "morph 400ms wizard → completion"
 *   - Tailwind transition utilities + prefers-reduced-motion
 *
 * Displays fullscreen celebration with:
 *   - Animated check mark
 *   - Headline + subheadline
 *   - CTA button to navigate to main panel
 *
 * Per .claude/rules/tessl__react-patterns: prefers-reduced-motion respected.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/cn";
import { WIZARD_COPY } from "../config/copy";

export interface WizardCompletionTransitionProps {
  /** Whether the completion state is active */
  isActive: boolean;
  /** Tenant ID for redirect path */
  tenantId?: string | null;
  /** Called after CTA is clicked (allows parent to handle redirect) */
  onNavigate?: () => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Fullscreen completion overlay with morph 400ms transition.
 * Respects prefers-reduced-motion.
 */
export function WizardCompletionTransition({
  isActive,
  onNavigate,
  className,
}: WizardCompletionTransitionProps) {
  const router = useRouter();
  const copy = WIZARD_COPY.completion;
  const [visible, setVisible] = useState(false);
  const [navigating, setNavigating] = useState(false);

  // Trigger entrance animation on mount when active
  useEffect(() => {
    if (isActive) {
      // Small delay to allow React to paint before starting transition
      const t = setTimeout(() => setVisible(true), 50);
      return () => clearTimeout(t);
    } else {
      setVisible(false);
    }
  }, [isActive]);

  const handleNavigate = () => {
    setNavigating(true);
    if (onNavigate) {
      onNavigate();
    } else {
      // Default: navigate to main app
      router.push("/");
    }
  };

  if (!isActive) return null;

  return (
    <div
      className={cn(
        "fixed inset-0 z-50 flex items-center justify-center",
        "bg-white",
        // Morph transition: fade in + scale up
        "transition-all duration-[400ms] ease-out",
        visible ? "opacity-100 scale-100" : "opacity-0 scale-95",
        "motion-reduce:transition-none motion-reduce:opacity-100 motion-reduce:scale-100",
        className,
      )}
      role="main"
      aria-live="assertive"
      aria-label={copy.headline}
    >
      <div className="max-w-md w-full text-center px-6 space-y-6">
        {/* Animated check mark */}
        <div
          className={cn(
            "mx-auto w-20 h-20 rounded-full flex items-center justify-center",
            "bg-gradient-to-br from-blue-700 to-purple-600",
            "shadow-lg",
            "transition-transform duration-500 ease-out",
            visible ? "scale-100" : "scale-0",
            "motion-reduce:scale-100 motion-reduce:transition-none",
          )}
          aria-hidden="true"
        >
          <svg
            width="36"
            height="36"
            viewBox="0 0 24 24"
            fill="none"
            stroke="white"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <polyline points="20,6 9,17 4,12" />
          </svg>
        </div>

        {/* Headline */}
        <div
          className={cn(
            "space-y-2",
            "transition-all duration-500 delay-200",
            visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4",
            "motion-reduce:opacity-100 motion-reduce:translate-y-0 motion-reduce:transition-none",
          )}
        >
          <h1 className="text-2xl font-bold text-gray-900">{copy.headline}</h1>
          <p className="text-base text-gray-600">{copy.subheadline}</p>
          <p className="text-sm text-gray-500 leading-relaxed">
            {copy.bodyText}
          </p>
        </div>

        {/* CTA */}
        <div
          className={cn(
            "transition-all duration-500 delay-300",
            visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4",
            "motion-reduce:opacity-100 motion-reduce:translate-y-0 motion-reduce:transition-none",
          )}
        >
          <button
            type="button"
            onClick={handleNavigate}
            disabled={navigating}
            className={cn(
              "rounded-2xl px-8 py-3 text-base font-semibold",
              "bg-gradient-to-r from-blue-700 to-purple-600 text-white",
              "hover:from-blue-800 hover:to-purple-700",
              "transition-all duration-150",
              "shadow-md hover:shadow-lg",
              "disabled:opacity-70 disabled:cursor-not-allowed",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600",
            )}
          >
            {navigating ? copy.ctaButtonLoading : copy.ctaButton}
          </button>
        </div>

        {/* Vitalia branding */}
        <div
          className={cn(
            "flex items-center justify-center gap-2",
            "transition-all duration-500 delay-400",
            visible ? "opacity-100" : "opacity-0",
            "motion-reduce:opacity-100 motion-reduce:transition-none",
          )}
          aria-hidden="true"
        >
          <span
            className={cn(
              "w-6 h-6 rounded-full flex items-center justify-center",
              "bg-gradient-to-br from-blue-700 to-purple-600",
              "text-white text-[10px] font-bold",
            )}
          >
            V
          </span>
          <span className="text-xs text-gray-400 font-medium">Vitalia</span>
        </div>
      </div>
    </div>
  );
}

WizardCompletionTransition.displayName = "WizardCompletionTransition";
