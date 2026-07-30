// cap: auth.sign-in-sign-up-pages
// story-origin: TBD
import type { Metadata } from "next";
import { SignIn } from "@clerk/nextjs";

export const metadata: Metadata = {
  title: "Iniciar sesión — Vitalia",
};

/**
 * Página de inicio de sesión — Clerk SignIn.
 *
 * SC-03: <SignIn /> renderizado, inputs email+contraseña visibles, sin placeholder.
 * SC-08: detecta ?error=no_tenants_assigned → muestra aviso administrativo.
 *
 * Apariencia alineada con design tokens Vitalia:
 *   colorPrimary  = var(--vitalia-cian-color)    [#01B2F8 — hero, CTA primario]
 *   colorText     = var(--vitalia-text-color)      [#1A1F36 — cuerpo principal]
 *   colorTextSecondary = var(--vitalia-text-muted-color)
 *   borderRadius  = 0.5rem (--vitalia-radius-md equivalente)
 *
 * spec_anchor: 03-arch-fe.md § 2.1 + 06-tickets.yaml T-3 SC-8
 * downstream-regression-na: brand-local page; no cross-brand consumers.
 */

interface SignInPageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function SignInPage({ searchParams }: SignInPageProps) {
  const resolvedParams = await searchParams;
  const errorCode = resolvedParams["error"];
  const hasNoTenantsError = errorCode === "no_tenants_assigned";

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-vitalia-bg p-6">
      {hasNoTenantsError && (
        <div
          className="w-full max-w-sm rounded-lg border border-amber-200 bg-amber-50 p-4 text-center dark:border-amber-800 dark:bg-amber-950"
          role="alert"
          data-testid="no-tenants-error"
        >
          <p className="text-sm font-semibold text-amber-800 dark:text-amber-200">
            Tu cuenta no tiene clínicas asignadas
          </p>
          <p className="mt-1 text-sm text-amber-700 dark:text-amber-300">
            Contacta al administrador de tu clínica para activar tu acceso.
          </p>
        </div>
      )}
      <SignIn
        appearance={{
          variables: {
            colorPrimary: "var(--vitalia-cian-color)",
            colorTextSecondary: "var(--vitalia-text-muted-color)",
            borderRadius: "0.5rem",
            fontFamily: "inherit",
          },
        }}
      />
    </main>
  );
}
