// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * SectionCard.tsx — contenedor de agrupación canónico para formularios de cuenta.
 *
 * Mismo wrapper visual que el patrón shipped de lisa/marca (IdentityCard.tsx:
 * `rounded-lg border border-border bg-card p-4 flex flex-col gap-4`) y que las
 * `section.card` del mockup ratificado (mockups/cuenta.html: 🏥 Identidad ·
 * 🧾 Identificación fiscal · 📍 Dirección y contacto · 🌎 Formato regional).
 *
 * Fix UI post-done 2026-06-12 (Chris): los campos estaban sueltos sobre el fondo
 * — se alejaba del mockup y del patrón de agrupación establecido en Mi Clínica/Marca.
 */

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface SectionCardProps {
  /** Título de la card (con emoji como el mockup, ej. "🏥 Identidad"). */
  title: string;
  /** id para aria-labelledby. */
  titleId: string;
  /** Descripción corta opcional bajo el título. */
  description?: string;
  children: ReactNode;
  className?: string;
}

/**
 * SectionCard — card de agrupación de campos (patrón marca/IdentityCard).
 */
export function SectionCard({ title, titleId, description, children, className }: SectionCardProps) {
  return (
    <section
      aria-labelledby={titleId}
      className={cn("rounded-lg border border-border bg-card p-4 flex flex-col gap-4", className)}
    >
      <div>
        <h2 id={titleId} className="text-sm font-semibold text-foreground">
          {title}
        </h2>
        {description && <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>}
      </div>
      {children}
    </section>
  );
}

SectionCard.displayName = "SectionCard";
