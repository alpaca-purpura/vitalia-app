// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * OnboardingStep3Client — Step 3 of 3-step clinic onboarding wizard.
 *
 * Bridge to launch the offer wizard (medical_services_v1 preset) as the first
 * offer creation during onboarding. Displays a call-to-action to start the
 * offer wizard or skip to dashboard. Uses useOfferCreate mutation.
 *
 * D9 pattern: Server Component page renders this Client Component.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { cn } from "@/lib/cn";
import { MICROCOPY_OFFER_WIZARD } from "@/features/vitalia/config/microcopy";

export interface OnboardingStep3ClientProps {
  onLaunchWizard: () => void;
  onSkip?: () => void;
  onBack: () => void;
  isLoading?: boolean;
}

export function OnboardingStep3Client({
  onLaunchWizard,
  onSkip,
  onBack,
  isLoading = false,
}: OnboardingStep3ClientProps) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">
          Tu primera oferta
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          Crea tu primera oferta médica para que los pacientes puedan agendarse.
        </p>
      </div>

      {/* Offer wizard CTA card */}
      <div className="rounded-lg border-2 border-blue-200 bg-blue-50 p-6 flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <span className="text-base font-semibold text-blue-900">
            {MICROCOPY_OFFER_WIZARD.title}
          </span>
          <span className="text-sm text-blue-700">
            Configura nombre, precio, prepago, consentimiento y profesional
            asignado.
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {["Tipo de servicio", "Precio", "Consentimiento", "Duración"].map(
            (step) => (
              <span
                key={step}
                className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700"
              >
                {step}
              </span>
            ),
          )}
        </div>

        <button
          type="button"
          onClick={onLaunchWizard}
          disabled={isLoading}
          aria-busy={isLoading}
          className={cn(
            "w-full px-6 py-2.5 rounded-md text-sm font-semibold transition-colors",
            "bg-blue-600 text-white hover:bg-blue-700",
            "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
            "disabled:opacity-50 disabled:cursor-not-allowed",
          )}
        >
          {isLoading ? "Iniciando..." : "Crear primera oferta"}
        </button>
      </div>

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
        {onSkip && (
          <button
            type="button"
            onClick={onSkip}
            disabled={isLoading}
            className={cn(
              "px-4 py-2 rounded-md text-sm font-medium text-gray-500 transition-colors",
              "hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500",
              "disabled:opacity-50 disabled:cursor-not-allowed",
            )}
          >
            Omitir por ahora
          </button>
        )}
      </div>
    </div>
  );
}
