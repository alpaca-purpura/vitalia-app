// cap: shell-organism.shell-vitalia
// story-origin: vitalia-bugfix-shell-nav-scroll-errors T-3
"use client";

/**
 * error.tsx — Generic route error boundary for ANY shell-organism [agent] segment.
 *
 * Bug #7 fix (vitalia-bugfix-shell-nav-scroll-errors T-3):
 *   Antes el ÚNICO error boundary del shell era mateo/agenda/error.tsx (una sola
 *   ruta). Un throw en el contenido de cualquier OTRA hoja burbujeaba por encima
 *   del shell layout hasta el error global de Next.js → reemplazaba la página
 *   entera → el chrome (Ribbon + SubTabsBar + ValeriaSidebar) moría → navegación
 *   bloqueada (botones muertos).
 *
 * Al vivir DENTRO de (shell-organism)/layout.tsx → ShellOrganismLayout →
 * AppPanelSlot (que renderiza Ribbon/SubTabsBar/SubSubTabsBar + {children}), este
 * boundary captura el error del sub-árbol [agent] y renderiza el fallback EN EL
 * SLOT DE CONTENIDO. El chrome y la navegación quedan vivos → el fallo se aísla al
 * panel. Botón "Reintentar" (reset()) re-monta el sub-árbol.
 *
 * Next.js App Router error.tsx contract:
 *   - MUST be "use client" (Next.js requirement).
 *   - MUST be a default export (Next.js requirement — excepción explícita al
 *     FSD-Lite no-default-export gate; mismo patrón que mateo/agenda/error.tsx).
 *   - Receives `error` (Error & { digest? }) and `reset` (() => void) props.
 *   - Shown when the [agent] segment or its children throw.
 *
 * NO-PHI log: solo error.message del render (no datos de paciente), igual que
 * mateo/agenda/error.tsx. El mensaje crudo solo se muestra en development.
 *
 * Spanish neutro LatAm — sin voseo.
 *
 * spec_anchor: 03-arch.md § Bug #7 + 06-tickets.yaml T-3
 * downstream-regression-na: brand-local route boundary; no cross-brand consumers
 */

import { useEffect } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

// ── Props (Next.js App Router error.tsx contract) ─────────────────────────────

interface AgentErrorBoundaryProps {
  error: Error & { digest?: string };
  reset: () => void;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Generic error fallback for any shell-organism agent sub-tree.
 * Renders inside the content panel (flex flex-1) — NOT full screen — so the shell
 * chrome (Ribbon + SubTabsBar + ValeriaSidebar) stays mounted and navigable.
 * Logs to console.error for observability (non-PHI).
 */
export default function AgentError({ error, reset }: AgentErrorBoundaryProps) {
  useEffect(() => {
    // Log to observability (non-PHI — error.message from route render, not patient data)
    console.error("[AgentError]", error);
  }, [error]);

  return (
    <div
      className="flex flex-1 flex-col items-center justify-center gap-4 p-8"
      role="alert"
      aria-live="assertive"
      data-testid="agent-error-boundary"
    >
      <Alert variant="destructive" className="w-full max-w-md">
        <AlertTriangle className="h-4 w-4" aria-hidden="true" />
        <AlertTitle>No se pudo cargar esta sección</AlertTitle>
        <AlertDescription>
          Ocurrió un problema al cargar esta vista. Puedes intentar recargarla; la
          navegación sigue disponible para moverte a otra sección.
          {process.env.NODE_ENV === "development" && error.message && (
            <span className="mt-2 block font-mono text-xs opacity-70">
              {error.message}
            </span>
          )}
        </AlertDescription>
      </Alert>

      <Button
        variant="outline"
        size="sm"
        onClick={reset}
        className="flex items-center gap-2"
        data-testid="agent-error-retry"
      >
        <RotateCcw className="h-4 w-4" aria-hidden="true" />
        Reintentar
      </Button>
    </div>
  );
}
