// canon: design-system-canon.md §6.2 · story-origin: core-ds-foundation
"use client";

/**
 * DashboardPageScaffold.tsx — Archetype "dashboard" (canon §6.2 · @luana/ui-kit).
 *
 * SCAFFOLD: arma PageHeader + un PageContentStack de bloques <PageSection/> +
 * estados, en la forma canónica de una hoja-dashboard (resumen + secciones).
 *
 * Slots:
 *   - `header`   → un <PageHeader/>
 *   - `children` → bloques <PageSection/> apilados (cada uno con su título H2)
 *
 * Estados (precedencia): error → loading → contenido.
 *
 * Named export (NO default).
 */

import * as React from "react";

import { cn } from "@luana/format/utils";

import { PageContainer, PageContentStack } from "../layout/page";
import { ErrorState } from "../layout/states";
import { FormPageSkeleton } from "../layout/skeletons";

export interface DashboardPageScaffoldProps {
  /** Encabezado de la hoja — típicamente un <PageHeader/>. */
  header: React.ReactNode;
  /** Muestra el esqueleto mientras carga. */
  isLoading?: boolean;
  /** Estado de error: si hay valor, reemplaza el contenido por un <ErrorState/>. */
  error?: React.ReactNode;
  /** Bloques de la hoja (<PageSection/>). */
  children?: React.ReactNode;
  /** Bloques placeholder del esqueleto (default 3). */
  skeletonSections?: number;
  className?: string;
}

/**
 * DashboardPageScaffold — hoja-dashboard canónica.
 * data-testid="dashboard-page-scaffold".
 */
export function DashboardPageScaffold({
  header,
  isLoading = false,
  error,
  children,
  skeletonSections = 3,
  className,
}: DashboardPageScaffoldProps) {
  let body: React.ReactNode;
  if (error) {
    body =
      typeof error === "boolean" ? (
        <ErrorState message="No se pudo cargar el panel." />
      ) : (
        error
      );
  } else if (isLoading) {
    body = <FormPageSkeleton sections={skeletonSections} data-testid="dashboard-page-scaffold-skeleton" />;
  } else {
    body = children;
  }

  return (
    <PageContainer data-testid="dashboard-page-scaffold" className={cn(className)}>
      <PageContentStack>
        {header}
        {body}
      </PageContentStack>
    </PageContainer>
  );
}

DashboardPageScaffold.displayName = "DashboardPageScaffold";
