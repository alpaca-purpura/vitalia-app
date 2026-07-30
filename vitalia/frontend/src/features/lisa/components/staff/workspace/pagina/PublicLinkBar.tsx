// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
"use client";
/**
 * PublicLinkBar.tsx — Pill badge + URL + copy + view + visibility toggle.
 *
 * States:
 *   - Publicada (visiblePublic=true): green pill + public URL + Copiar + Ver
 *   - Borrador (visiblePublic=false | no slug): grey pill + "(URL no disponible)" + disable Ver
 *
 * Anti-enumeration (RN-D3D-9): toggle OFF keeps same page at /d/... but BE
 * returns identical "perfil no disponible" for toggle-OFF/unknown/cross-tenant.
 *
 * URL source: NEXT_PUBLIC_APP_BASE_URL env var (never hardcoded).
 * Accessible: status communicated via aria-live + button aria-label.
 *
 * T-FE-pagina-publica vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-D.4
 */

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useTogglePublicVisible } from "../../../../api/staff";
import { cn } from "@/lib/utils";
import type { DoctorDetail } from "../../../../types/staff.types";

interface PublicLinkBarProps {
  doctorId: string;
  doctor: DoctorDetail;
}

/** Base app URL from env — required for absolute public link */
const APP_BASE_URL = process.env.NEXT_PUBLIC_APP_BASE_URL ?? "";

/**
 * PublicLinkBar — visibility pill + URL + actions + toggle.
 */
export function PublicLinkBar({ doctorId, doctor }: PublicLinkBarProps) {
  const toggleMutation = useTogglePublicVisible(doctorId);
  const [copied, setCopied] = useState(false);

  const isPublic = doctor.visibleEnLanding === true;
  const hasSlug = !!doctor.publicSlug && !!doctor.clinicSlug;

  // Derive public URL — only if both slug and clinicSlug are available.
  // clinicSlug is not in DoctorDetail; we use a placeholder path fragment.
  // In practice, the BE populates publicSlug only when clinic slug exists.
  // For the link we use the /d/ public route pattern.
  const publicUrl = hasSlug
    ? `${APP_BASE_URL}/d/${doctor.clinicSlug}/${doctor.publicSlug}`
    : null;

  async function handleCopy() {
    if (!publicUrl) return;
    await navigator.clipboard.writeText(publicUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleToggle() {
    void toggleMutation.mutate(!isPublic);
  }

  return (
    <article
      className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-border bg-card p-4"
      data-testid="public-link-bar"
      aria-label="Estado de publicación del perfil"
    >
      {/* Left: status pill + URL */}
      <header className="flex flex-col gap-1.5 min-w-0">
        {/* Status pill */}
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
              isPublic
                ? "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300"
                : "bg-muted text-muted-foreground",
            )}
            aria-live="polite"
            aria-label={isPublic ? "Perfil publicado" : "Perfil en borrador"}
          >
            {isPublic ? "Publicada" : "Borrador"}
          </span>
          {toggleMutation.isPending && (
            <span className="text-xs text-muted-foreground">Actualizando...</span>
          )}
        </div>

        {/* URL display */}
        {publicUrl ? (
          <p
            className="text-xs text-muted-foreground truncate font-mono max-w-80"
            title={publicUrl}
            aria-label="Dirección web del perfil público"
          >
            {publicUrl}
          </p>
        ) : (
          <p className="text-xs text-muted-foreground italic">
            URL no disponible (perfil sin generar)
          </p>
        )}
      </header>

      {/* Right: actions */}
      <nav className="flex items-center gap-2 shrink-0" aria-label="Acciones del perfil público">
        {/* Copy */}
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-8 text-xs"
          disabled={!publicUrl}
          onClick={() => void handleCopy()}
          aria-label="Copiar enlace del perfil público"
        >
          {copied ? "¡Copiado!" : "Copiar enlace"}
        </Button>

        {/* View (opens new tab) */}
        {publicUrl && isPublic ? (
          <Link
            href={publicUrl}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Ver perfil público en nueva pestaña"
          >
            <Button type="button" variant="outline" size="sm" className="h-8 text-xs">
              Ver
            </Button>
          </Link>
        ) : (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-8 text-xs"
            disabled
            aria-label="Ver perfil público (no disponible en borrador)"
          >
            Ver
          </Button>
        )}

        {/* Toggle visibility */}
        <Button
          type="button"
          size="sm"
          disabled={!hasSlug || toggleMutation.isPending}
          onClick={handleToggle}
          className={cn(
            "h-8 text-xs",
            isPublic
              ? "bg-muted text-foreground hover:bg-muted/80"
              : "bg-agent-lisa hover:bg-agent-lisa/90 text-white",
          )}
          aria-label={isPublic ? "Ocultar perfil (pasar a borrador)" : "Publicar perfil"}
        >
          {isPublic ? "Ocultar" : "Publicar"}
        </Button>
      </nav>

      {toggleMutation.isError && (
        <p className="w-full text-xs text-destructive" role="alert">
          Error al cambiar visibilidad. Vuelve a intentarlo.
        </p>
      )}
    </article>
  );
}
