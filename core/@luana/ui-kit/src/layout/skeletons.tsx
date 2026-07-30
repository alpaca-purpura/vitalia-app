// canon: design-system-canon.md §2.7 · story-origin: core-ds-foundation
import * as React from "react";

import { cn } from "@luana/format/utils";

import { Skeleton } from "../skeleton";

export interface ListPageSkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  rows?: number;
}

/** Esqueleto de una lista: N filas placeholder. */
export function ListPageSkeleton({ rows = 6, className, ...props }: ListPageSkeletonProps) {
  return (
    <div className={cn("flex flex-col gap-3", className)} {...props}>
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} data-testid="list-skeleton-row" className="h-14 w-full" />
      ))}
    </div>
  );
}

export interface FormPageSkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  sections?: number;
}

/** Esqueleto de un formulario: N secciones placeholder. */
export function FormPageSkeleton({ sections = 3, className, ...props }: FormPageSkeletonProps) {
  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      {Array.from({ length: sections }).map((_, i) => (
        <div key={i} data-testid="form-skeleton-section" className="flex flex-col gap-3">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ))}
    </div>
  );
}
