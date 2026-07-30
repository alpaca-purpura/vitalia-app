// canon: design-system-canon.md §2.7 · story-origin: core-ds-foundation
import * as React from "react";

import { cn } from "@luana/format/utils";

import { Button } from "../button";

export interface PaginationProps extends React.HTMLAttributes<HTMLElement> {
  page: number;
  pageCount: number;
  onPrev: () => void;
  onNext: () => void;
  prevLabel?: string;
  nextLabel?: string;
}

/** Paginación: anterior / siguiente + indicador "Página X de Y" + estados deshabilitados. */
export function Pagination({
  page,
  pageCount,
  onPrev,
  onNext,
  prevLabel = "Anterior",
  nextLabel = "Siguiente",
  className,
  ...props
}: PaginationProps) {
  return (
    <nav aria-label="Paginación" className={cn("flex items-center justify-between gap-4", className)} {...props}>
      <Button variant="outline" size="sm" onClick={onPrev} disabled={page <= 1}>
        {prevLabel}
      </Button>
      <span className="text-sm text-muted-foreground" aria-live="polite">
        Página {page} de {pageCount}
      </span>
      <Button variant="outline" size="sm" onClick={onNext} disabled={page >= pageCount}>
        {nextLabel}
      </Button>
    </nav>
  );
}
