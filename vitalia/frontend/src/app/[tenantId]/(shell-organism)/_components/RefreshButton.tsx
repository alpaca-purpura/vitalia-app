// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s9-TBD
/**
 * RefreshButton — Client Component leaf.
 *
 * Justificación "use client": usa useRouter().refresh() para forzar
 * re-fetch de Server Components en la ruta actual sin recargar la página.
 *
 * Renderizado como hoja dentro del árbol Server Component de NetworkErrorFallback.
 * No recibe ni expone datos de sesión ni PHI.
 *
 * spec_anchor: 03-arch-fe.md § 2.1 + 06-tickets.yaml T-3 (SC-7 network fallback)
 * downstream-regression-na: brand-local _component; no cross-brand consumers.
 */

"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

/**
 * Botón de reintento — llama router.refresh() para re-ejecutar
 * el Server Component padre y reintentar la carga del tenant.
 */
export function RefreshButton() {
  const router = useRouter();

  return (
    <Button
      onClick={() => router.refresh()}
      data-testid="network-error-retry"
      variant="default"
      className="mt-4"
    >
      Reintentar
    </Button>
  );
}
