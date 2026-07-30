// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * OnboardingStep2Client — Step 2 of 3-step clinic onboarding wizard.
 *
 * Displays available plan tiers (from usePlanTiers hook) for selection.
 * Loading/error/empty states included per tessl__react-patterns.
 * D9 pattern: Server Component page renders this Client Component.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";
import { usePlanTiers } from "@/features/vitalia/api/use-plan-tiers";

export interface OnboardingStep2ClientProps {
  onNext: (planSlug: string) => void;
  onBack: () => void;
  isLoading?: boolean;
}

export function OnboardingStep2Client({
  onNext,
  onBack,
  isLoading = false,
}: OnboardingStep2ClientProps) {
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading: isLoadingPlans, isError } = usePlanTiers();

  function handleNext() {
    if (!selectedPlan) {
      setError("Selecciona un plan para continuar");
      return;
    }
    setError(null);
    onNext(selectedPlan);
  }

  if (isLoadingPlans) {
    return (
      <div
        className="flex flex-col gap-4"
        aria-busy="true"
        aria-label="Cargando planes"
      >
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-24 rounded-lg border border-gray-200 bg-gray-100 animate-pulse"
            aria-hidden="true"
          />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div
        role="alert"
        className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
      >
        <p className="font-medium">No se pudieron cargar los planes.</p>
        <p className="mt-1 text-xs">Intenta recargar la página.</p>
      </div>
    );
  }

  const plans = data?.plans ?? [];

  if (plans.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-6 text-center text-sm text-gray-500">
        No hay planes disponibles en este momento.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Elige tu plan</h2>
        <p className="text-sm text-gray-500 mt-1">
          Puedes cambiar tu plan en cualquier momento.
        </p>
      </div>

      {/* Plan cards */}
      <div
        className="flex flex-col gap-3"
        role="radiogroup"
        aria-label="Planes disponibles"
        aria-required="true"
      >
        {plans.map((plan) => {
          const isSelected = selectedPlan === plan.slug;
          return (
            <label
              key={plan.slug}
              className={cn(
                "relative flex flex-col gap-2 p-4 rounded-lg border-2 cursor-pointer transition-all",
                "hover:border-blue-400",
                isSelected
                  ? "border-blue-600 bg-blue-50"
                  : "border-gray-200 bg-white",
                isLoading &&
                  "opacity-50 cursor-not-allowed pointer-events-none",
              )}
            >
              <input
                type="radio"
                name="plan"
                value={plan.slug}
                checked={isSelected}
                onChange={() => {
                  setSelectedPlan(plan.slug);
                  setError(null);
                }}
                disabled={isLoading}
                aria-label={plan.label_es}
                className="sr-only"
              />
              <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-900 text-sm">
                  {plan.label_es}
                </span>
                <span className="text-sm font-bold text-blue-700">
                  {plan.price_usd_monthly === 0
                    ? "Gratis"
                    : `USD ${plan.price_usd_monthly}/mes`}
                </span>
              </div>
              <span className="text-xs text-gray-500">
                Hasta {plan.included_user_count}{" "}
                {plan.included_user_count === 1 ? "usuario" : "usuarios"}
              </span>
              {plan.features_enabled.length > 0 && (
                <ul className="flex flex-wrap gap-1 mt-1">
                  {plan.features_enabled.slice(0, 3).map((feat) => (
                    <li
                      key={feat}
                      className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700"
                    >
                      {feat.replace(/_/g, " ")}
                    </li>
                  ))}
                </ul>
              )}
              {isSelected && (
                <span
                  className="absolute top-3 right-3 w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center"
                  aria-hidden="true"
                >
                  <span className="w-2.5 h-2.5 rounded-full bg-white" />
                </span>
              )}
            </label>
          );
        })}
      </div>

      {error && (
        <p role="alert" className="text-xs text-red-600">
          {error}
        </p>
      )}

      {/* Navigation */}
      <div className="flex justify-between items-center pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={onBack}
          disabled={isLoading}
          className={cn(
            "px-4 py-2 rounded-md text-sm font-medium transition-colors",
            "border border-gray-300 text-gray-700 hover:bg-gray-50",
            "focus:outline-none focus:ring-2 focus:ring-blue-500",
            "disabled:opacity-50 disabled:cursor-not-allowed",
          )}
        >
          Atrás
        </button>
        <button
          type="button"
          onClick={handleNext}
          disabled={isLoading || !selectedPlan}
          aria-busy={isLoading}
          className={cn(
            "px-6 py-2 rounded-md text-sm font-medium transition-colors",
            "bg-blue-600 text-white hover:bg-blue-700",
            "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
            "disabled:opacity-50 disabled:cursor-not-allowed",
          )}
        >
          {isLoading ? "Procesando..." : "Siguiente"}
        </button>
      </div>
    </div>
  );
}
