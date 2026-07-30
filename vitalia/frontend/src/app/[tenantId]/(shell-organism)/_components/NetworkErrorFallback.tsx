// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s9-TBD
/**
 * NetworkErrorFallback — Server Component.
 *
 * Renderizado cuando fetchUserTenants() lanza un error de red en layout.tsx.
 * No contiene estado ni efectos — puro Server Component.
 *
 * Incluye RefreshButton (Client leaf) como único elemento interactivo.
 * La hoja "use client" está justificada por useRouter().refresh().
 *
 * Microcopy (spec § 10 verbatim):
 *   Título: "Estamos teniendo problemas conectando con el servidor"
 *   Descripción: "Intenta de nuevo en unos segundos."
 *   CTA: "Reintentar"
 *
 * HIPAA-lite: no muestra PHI — solo mensaje de error de conectividad.
 * spec_anchor: 03-arch-fe.md § 2.1 + 06-tickets.yaml T-3 (SC-7)
 * downstream-regression-na: brand-local _component; no cross-brand consumers.
 */

import { RefreshButton } from "./RefreshButton";

/**
 * Fallback de error de red para el shell organism.
 * Se muestra cuando el servidor IAM no responde durante la carga del layout.
 */
export function NetworkErrorFallback() {
  return (
    <main
      className="flex min-h-screen flex-col items-center justify-center gap-3 p-6 text-center"
      data-testid="network-error-fallback"
    >
      <span className="text-4xl" role="img" aria-label="Advertencia">
        ⚠️
      </span>
      <h1 className="text-xl font-semibold text-foreground">
        Estamos teniendo problemas conectando con el servidor
      </h1>
      <p className="text-sm text-muted-foreground">
        Intenta de nuevo en unos segundos.
      </p>
      <RefreshButton />
    </main>
  );
}
