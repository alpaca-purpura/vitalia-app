// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * TypographyEditor.tsx — Heading + body font selectors with live preview.
 *
 * Two selectors (heading + body) with a set of common fonts loaded via
 * CSS @font-face / Google Fonts suggestion text.
 * Autosave 600ms via RHF watch → scheduleAutosave callback.
 *
 * Renders a live preview paragraph to show the font in context.
 *
 * Spanish neutro LatAm — no voseo.
 *
 * T-5 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-5 deliverables
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */


import { useCallback, useEffect } from "react";
import { cn } from "@/lib/utils";

/**
 * Carga una familia de Google Fonts on-demand para que la vista previa pueda
 * renderizarla. Sin esto, el `font-family` del preview cae a sans-serif (la fuente
 * no está cargada) y el texto se ve igual elijas la que elijas. Idempotente por
 * familia. `display=swap` evita el flash de texto invisible.
 *
 * Nota prod (HIPAA-lite): es config de marca (no PHI). Para prod conviene
 * self-hostear las fuentes (next/font) en vez del CDN de Google.
 */
function ensureGoogleFont(family: string): void {
  if (typeof document === "undefined") return;
  const id = `gfont-${family.replace(/\s+/g, "-").toLowerCase()}`;
  if (document.getElementById(id)) return;
  const link = document.createElement("link");
  link.id = id;
  link.rel = "stylesheet";
  link.href = `https://fonts.googleapis.com/css2?family=${family.replace(/ /g, "+")}:wght@400;600&display=swap`;
  document.head.appendChild(link);
}

const FONT_OPTIONS = [
  { value: "Inter", label: "Inter" },
  { value: "Roboto", label: "Roboto" },
  { value: "Open Sans", label: "Open Sans" },
  { value: "Lato", label: "Lato" },
  { value: "Montserrat", label: "Montserrat" },
  { value: "Poppins", label: "Poppins" },
  { value: "Nunito", label: "Nunito" },
  { value: "Source Sans 3", label: "Source Sans 3" },
  { value: "Merriweather", label: "Merriweather" },
  { value: "Playfair Display", label: "Playfair Display" },
] as const;

export interface TypographyEditorProps {
  headingFont?: string;
  bodyFont?: string;
  onChangeHeading?: (font: string) => void;
  onChangeBody?: (font: string) => void;
  className?: string;
}

/**
 * TypographyEditor — heading + body font selectors with live preview.
 */
export function TypographyEditor({
  headingFont,
  bodyFont,
  onChangeHeading,
  onChangeBody,
  className,
}: TypographyEditorProps) {
  const handleHeadingChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      onChangeHeading?.(e.target.value);
    },
    [onChangeHeading],
  );

  const handleBodyChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      onChangeBody?.(e.target.value);
    },
    [onChangeBody],
  );

  const displayHeading = headingFont ?? FONT_OPTIONS[0].value;
  const displayBody = bodyFont ?? FONT_OPTIONS[0].value;

  // Carga las fuentes seleccionadas para que el preview las renderice de verdad.
  useEffect(() => {
    ensureGoogleFont(displayHeading);
    ensureGoogleFont(displayBody);
  }, [displayHeading, displayBody]);

  return (
    <section
      aria-label="Tipografía de la marca"
      className={cn("rounded-lg border border-border bg-card p-4 flex flex-col gap-4", className)}
    >
      <div>
        <h3 className="text-sm font-semibold text-foreground">Tipografía</h3>
        <p className="text-xs text-muted-foreground mt-0.5">
          Fuentes para títulos y texto de cuerpo.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {/* Heading font */}
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="heading-font-select"
            className="text-xs font-medium text-foreground"
          >
            Fuente de títulos
          </label>
          <select
            id="heading-font-select"
            value={displayHeading}
            onChange={handleHeadingChange}
            className={cn(
              "rounded-md border border-border bg-background px-3 py-1.5",
              "text-sm text-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            )}
            aria-label="Seleccionar fuente de títulos"
          >
            {FONT_OPTIONS.map((font) => (
              <option key={font.value} value={font.value}>
                {font.label}
              </option>
            ))}
          </select>
        </div>

        {/* Body font */}
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="body-font-select"
            className="text-xs font-medium text-foreground"
          >
            Fuente de cuerpo
          </label>
          <select
            id="body-font-select"
            value={displayBody}
            onChange={handleBodyChange}
            className={cn(
              "rounded-md border border-border bg-background px-3 py-1.5",
              "text-sm text-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            )}
            aria-label="Seleccionar fuente de texto de cuerpo"
          >
            {FONT_OPTIONS.map((font) => (
              <option key={font.value} value={font.value}>
                {font.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Live preview */}
      <div
        aria-label="Vista previa de tipografía"
        className="rounded-md border border-border bg-muted/20 p-3"
      >
        <p
          className="text-base font-semibold text-foreground"
          style={{ fontFamily: `"${displayHeading}", sans-serif` }}
        >
          Clínica Dental Lima Centro
        </p>
        <p
          className="mt-1 text-sm text-muted-foreground"
          style={{ fontFamily: `"${displayBody}", sans-serif` }}
        >
          Tu salud bucal es nuestra prioridad. Agenda tu consulta hoy.
        </p>
      </div>
    </section>
  );
}

TypographyEditor.displayName = "TypographyEditor";
