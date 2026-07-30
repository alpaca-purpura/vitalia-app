// canon: design-system-canon.md §2.7 · story-origin: core-ds-foundation
import * as React from "react";

import { cn } from "@luana/format/utils";

/** Barra horizontal de acciones: búsqueda + toggles + filtros. */
export function Toolbar({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div role="toolbar" className={cn("flex flex-wrap items-center gap-2", className)} {...props}>
      {children}
    </div>
  );
}

export interface FilterBarProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "children"> {
  search?: React.ReactNode;
  sort?: React.ReactNode;
  viewMode?: React.ReactNode;
  children?: React.ReactNode;
}

/** Barra de filtros: búsqueda a la izquierda, orden + modo de vista a la derecha. */
export function FilterBar({ search, sort, viewMode, className, children, ...props }: FilterBarProps) {
  return (
    <Toolbar className={cn("justify-between", className)} {...props}>
      <div className="flex flex-1 items-center gap-2">
        {search}
        {children}
      </div>
      {(sort || viewMode) ? (
        <div className="flex items-center gap-2">
          {sort}
          {viewMode}
        </div>
      ) : null}
    </Toolbar>
  );
}
