// canon: design-system-canon.md §2.7 · story-origin: core-ds-foundation
import * as React from "react";

import { cn } from "@luana/format/utils";

/** Contenido de detalle: columna única de ancho legible. */
export function DetailLayout({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("mx-auto w-full max-w-3xl", className)} {...props}>
      {children}
    </div>
  );
}

export interface FormLayoutProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 2 columnas SOLO cuando los campos están conceptualmente pareados. */
  paired?: boolean;
}

/** Contenido de formulario: 1-col por defecto; 2-col solo para campos pareados. */
export function FormLayout({ paired = false, className, children, ...props }: FormLayoutProps) {
  return (
    <div
      className={cn(paired ? "grid grid-cols-1 gap-6 md:grid-cols-2" : "flex flex-col gap-6", className)}
      {...props}
    >
      {children}
    </div>
  );
}
