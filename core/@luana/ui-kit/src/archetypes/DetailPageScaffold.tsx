// canon: design-system-canon.md §6.2 · story-origin: core-ds-foundation
"use client";

/**
 * DetailPageScaffold.tsx — Archetype "detalle" (canon §6.2 · @luana/ui-kit).
 *
 * SCAFFOLD: arma la franja N3 (EntitySubNavBar, vía slot) + el contenido de
 * detalle (DetailLayout) + estados, en la forma canónica de una hoja-detalle.
 *
 * Router-free: el scaffold NO lee next/navigation. El consumidor pasa el ribbon
 * ya montado en `subnav` (un <EntitySubNavBar/> o un <EntityWorkspaceLayout/>),
 * o un `header` simple. Así el archetype permanece testeable sin mocks de router.
 *
 * Slots:
 *   - `subnav`   → franja N3 full-bleed (default: ninguna)
 *   - `header`   → header alternativo cuando no hay franja N3
 *   - `children` → contenido del leaf activo (envuelto en <DetailLayout/>)
 *
 * Estados (precedencia): error → loading → contenido.
 *
 * Named export (NO default).
 */

import * as React from "react";

import { cn } from "@luana/format/utils";

import { PageContainer } from "../layout/page";
import { DetailLayout } from "../layout/layouts";
import { ErrorState } from "../layout/states";
import { FormPageSkeleton } from "../layout/skeletons";

export interface DetailPageScaffoldProps {
  /** Franja N3 full-bleed (típicamente un <EntitySubNavBar/>). Va fuera del padding. */
  subnav?: React.ReactNode;
  /** Header alternativo cuando no hay franja N3 (típicamente un <PageHeader/>). */
  header?: React.ReactNode;
  /** Muestra el esqueleto mientras carga. */
  isLoading?: boolean;
  /** Estado de error: si hay valor, reemplaza el contenido por un <ErrorState/>. */
  error?: React.ReactNode;
  /** Contenido del leaf activo. */
  children?: React.ReactNode;
  className?: string;
}

/**
 * DetailPageScaffold — hoja-detalle canónica.
 * data-testid="detail-page-scaffold".
 */
export function DetailPageScaffold({
  subnav,
  header,
  isLoading = false,
  error,
  children,
  className,
}: DetailPageScaffoldProps) {
  let body: React.ReactNode;
  if (error) {
    body =
      typeof error === "boolean" ? (
        <ErrorState message="No se pudo cargar el detalle." />
      ) : (
        error
      );
  } else if (isLoading) {
    body = <FormPageSkeleton data-testid="detail-page-scaffold-skeleton" />;
  } else {
    body = children;
  }

  return (
    <div
      data-testid="detail-page-scaffold"
      className={cn("flex flex-col flex-1 min-h-0", className)}
    >
      {/* Franja N3 full-bleed — fuera del padding (canon §2.2). */}
      {subnav}
      <PageContainer data-testid="detail-page-scaffold-content">
        {header ? <div className="mb-6">{header}</div> : null}
        <DetailLayout>{body}</DetailLayout>
      </PageContainer>
    </div>
  );
}

DetailPageScaffold.displayName = "DetailPageScaffold";
