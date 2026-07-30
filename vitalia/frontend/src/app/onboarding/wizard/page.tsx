// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
/**
 * /onboarding/wizard — Wizard onboarding entry page.
 *
 * Pure Server Component (no "use client"). Delegates all interactivity
 * to WizardOnboardingLayout (Client Component).
 *
 * Per tessl__nextjs-app-router-modularization:
 *   - This page renders a single Client Component subtree.
 *   - metadata exported from Server Component (safe).
 *   - No hooks, no state, no event handlers here.
 *
 * downstream-regression-na: brand-local FE page; no cross-brand consumers
 */

import { Suspense } from "react";
import type { Metadata } from "next";
import { WizardOnboardingLayout } from "@/features/onboarding";

export const metadata: Metadata = {
  title: "Configuración de tu clínica — Vitalia",
  description:
    "Configura el perfil de tu clínica para personalizar tu asistente Vitalia.",
  robots: { index: false, follow: false },
};

/**
 * Wizard onboarding page — fullscreen immersive setup experience.
 * No page padding applied (wizard is fullscreen by design).
 */
export default function WizardOnboardingPage() {
  // Suspense boundary: WizardOnboardingLayout (cliente) usa useSearchParams; sin
  // el boundary, `next build` falla el prerender estático (CSR-bailout). Con él,
  // el shell estático renderiza y la isla cliente hidrata.
  return (
    <Suspense>
      <WizardOnboardingLayout />
    </Suspense>
  );
}
