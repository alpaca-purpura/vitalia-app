// cap: __shared__
// story-origin: TBD
/**
 * NotFoundShell — Outer 404 page (Server Component).
 * F1-S9 vitalia-fase1-routing-shell — T-4
 *
 * Renderiza cuando el agent slug en la URL no es válido.
 * Ejemplo: /{tenantId}/foo → isValidAgent("foo") = false → notFound() →
 * Next.js renderiza este archivo.
 *
 * Sin chrome shell (sin TopBar, sin Ribbon, sin ValeriaSidebar).
 * Llena el viewport — centrado verticalmente.
 *
 * Server Component puro — sin hooks, sin "use client".
 * No recibe params como función arg (Next.js no-found.tsx convention).
 * Para navegar back → href "/" que el root page redirige a /{tenantId}/{DEFAULT_LANDING_SUBPATH}
 * (= mateo/agenda v1.2; antes valeria/agenda → 404, Bug #1 T-1).
 *
 * Microcopy spec: 01-spec.md § 10 (Spanish neutro LatAm — sin voseo).
 * A11y: role="main" + aria-hidden en emoji + focus visible via Shadcn Button.
 *
 * spec_anchor: 03-arch-fe.md T-4 + 01-spec.md § 6.1 + § 10 + § 12
 * downstream-regression-na: brand-local route; no cross-brand consumers.
 */

import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function NotFoundShell() {
  return (
    <main
      className="flex min-h-screen flex-col items-center justify-center gap-6 p-8"
      data-testid="not-found-shell"
      role="main"
    >
      {/* Ícono — aria-hidden per 01-spec.md § 12 */}
      <span
        aria-hidden="true"
        className="text-5xl opacity-50"
        role="img"
        aria-label="Advertencia"
      >
        🔍
      </span>

      <div className="flex flex-col items-center gap-3 text-center">
        <h1 className="text-2xl font-semibold tracking-tight">
          No encontramos esta vista
        </h1>
        <p className="max-w-sm text-muted-foreground text-sm">
          Quizás el enlace está roto o el agente que buscas no existe en esta
          clínica.
        </p>
      </div>

      {/* CTA — Button default + asChild + Link para SPA navigation */}
      <Button asChild>
        <Link href="/">Volver al inicio</Link>
      </Button>
    </main>
  );
}
