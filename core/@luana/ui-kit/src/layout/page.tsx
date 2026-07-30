// canon: design-system-canon.md §2.7 · story-origin: core-ds-foundation
import * as React from "react";

import { cn } from "@luana/format/utils";

/** Cuerpo de una hoja: padding interior estándar del shell (≈1.25rem 1.5rem). */
export function PageContainer({ className, children, ...props }: React.HTMLAttributes<HTMLElement>) {
  return (
    <section className={cn("px-6 py-5", className)} {...props}>
      {children}
    </section>
  );
}

/** Gestor de espaciado vertical uniforme entre bloques de una hoja. */
export function PageContentStack({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      {children}
    </div>
  );
}

export interface PageHeaderProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "title"> {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  /**
   * Etiqueta de la afordancia de regreso (ej. "Agenda"). Cuando está presente, el
   * encabezado se renderiza como FRANJA N3 FULL-BLEED (sticky top, bg-card,
   * border-bottom, radius:0 — mismo lenguaje visual que EntitySubNavBar · canon
   * §1.2/§2.2) con el pill «‹ {backLabel}» a la IZQUIERDA (regreso/descarte) +
   * título·subtítulo inline. Aditivo: sin `backLabel` es el encabezado de contenido
   * estándar (título prominente + acciones a la derecha).
   */
  backLabel?: string;
  /** Click en el pill de regreso. */
  onBack?: () => void;
  /** Nodo opcional a la izquierda del título (dot de agente / ícono). */
  leading?: React.ReactNode;
}

/** Encabezado de página: pill de regreso opcional + título + subtítulo + acciones (flex-between). */
export function PageHeader({
  title,
  subtitle,
  actions,
  backLabel,
  onBack,
  leading,
  className,
  ...props
}: PageHeaderProps) {
  // Hoja-leaf alcanzada desde un padre (backLabel presente): se renderiza como
  // FRANJA N3 FULL-BLEED — mismo lenguaje visual que EntitySubNavBar (canon §1.2/§2.2):
  // sticky top, bg-card, border-bottom, radius:0, el pill «‹ {backLabel}» a la IZQUIERDA
  // (afordancia de regreso/descarte), título+subtítulo inline. NO un encabezado de
  // contenido con padding ni un pill flotante sobre el título.
  if (backLabel) {
    return (
      <div
        className={cn(
          "sticky top-0 z-20 w-full rounded-none border-b border-border bg-card",
          "flex min-h-[44px] items-center gap-3 px-4",
          className,
        )}
        {...props}
      >
        <button
          type="button"
          onClick={onBack}
          data-testid="page-header-back"
          className={cn(
            "inline-flex shrink-0 items-center gap-1 rounded-md px-3 py-1.5 text-sm font-medium",
            "text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
          )}
        >
          <span aria-hidden="true" className="text-muted-foreground">
            ‹
          </span>
          {backLabel}
        </button>
        {leading ? <div className="shrink-0">{leading}</div> : null}
        <div className="flex min-w-0 items-baseline gap-2">
          <h1 className="truncate text-sm font-semibold text-foreground">{title}</h1>
          {subtitle ? (
            <span className="truncate text-xs text-muted-foreground">{subtitle}</span>
          ) : null}
        </div>
        {actions ? <div className="ml-auto flex shrink-0 items-center gap-2">{actions}</div> : null}
      </div>
    );
  }

  // Encabezado de contenido estándar (sin backLabel): título prominente + acciones a la derecha.
  return (
    <div className={cn("flex items-start justify-between gap-4", className)} {...props}>
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          {leading ? <div className="shrink-0">{leading}</div> : null}
          <h1 className="truncate text-lg font-semibold text-foreground">{title}</h1>
        </div>
        {subtitle ? <p className="text-sm text-muted-foreground">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
  );
}

export interface PageSectionProps extends Omit<React.HTMLAttributes<HTMLElement>, "title"> {
  title?: React.ReactNode;
}

/** Sección semántica con título H2 opcional + bloque de contenido. */
export function PageSection({ title, children, className, ...props }: PageSectionProps) {
  const headingId = React.useId();
  return (
    <section
      className={cn("flex flex-col gap-3", className)}
      aria-labelledby={title ? headingId : undefined}
      {...props}
    >
      {title ? (
        <h2 id={headingId} className="text-base font-medium text-foreground">
          {title}
        </h2>
      ) : null}
      {children}
    </section>
  );
}
