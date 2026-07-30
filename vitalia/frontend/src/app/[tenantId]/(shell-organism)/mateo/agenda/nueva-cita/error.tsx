// cap: scheduling.mateo-agenda
/**
 * error.tsx — Route error boundary for the nueva-cita leaf sheet.
 * T-FE-1 vitalia-fase2-mateo-nueva-cita
 *
 * MUST be "use client" (Next.js App Router error.tsx requirement).
 */

"use client";

import { useEffect } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

interface NuevaCitaErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function NuevaCitaError({ error, reset }: NuevaCitaErrorProps) {
  useEffect(() => {
    console.error("[NuevaCitaError]", error);
  }, [error]);

  return (
    <div
      className="flex flex-1 flex-col items-center justify-center gap-4 p-8"
      role="alert"
      aria-live="assertive"
    >
      <Alert variant="destructive" className="max-w-md w-full">
        <AlertTriangle className="h-4 w-4" aria-hidden="true" />
        <AlertTitle>Error al cargar el formulario</AlertTitle>
        <AlertDescription>
          No se pudo cargar la pantalla de nueva cita. Puedes intentar
          recargar o volver a la agenda.
          {process.env.NODE_ENV === "development" && error.message && (
            <span className="block mt-2 text-xs font-mono opacity-70">
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
      >
        <RotateCcw className="h-4 w-4" aria-hidden="true" />
        Reintentar
      </Button>
    </div>
  );
}
