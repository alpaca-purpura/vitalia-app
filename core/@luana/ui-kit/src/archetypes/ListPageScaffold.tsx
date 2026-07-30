// canon: design-system-canon.md §6.2 · story-origin: core-ds-foundation
"use client";

/**
 * ListPageScaffold.tsx — Archetype "lista" (canon §6.2 · @luana/ui-kit).
 *
 * SCAFFOLD: arma las primitivas (PageHeader + toolbar/filtros + grilla de
 * EntityInfoCard + estados) en la forma canónica de una hoja-lista. El consumidor
 * SOLO rellena slots (no maqueta layout bespoke):
 *   - `header`      → un <PageHeader/> (título + acciones)
 *   - `toolbar`     → un <Toolbar/> o <FilterBar/> (búsqueda + filtros)
 *   - `children`    → las <EntityInfoCard/> de la grilla
 *   - `emptyState`  → contenido de vacío (default: <EmptyState/> neutro)
 *   - `pagination`  → un <Pagination/> opcional al pie
 *
 * Estados (precedencia): error → loading → empty → contenido.
 * La grilla usa `grid auto-fill minmax(250px,1fr)` (canon §2.3).
 *
 * Named export (NO default).
 */

import * as React from "react";

import { cn } from "@luana/format/utils";

import { PageContainer, PageContentStack } from "../layout/page";
import { EmptyState, ErrorState } from "../layout/states";
import { ListPageSkeleton } from "../layout/skeletons";

export interface ListPageScaffoldProps {
  /** Encabezado de la hoja — típicamente un <PageHeader/>. */
  header: React.ReactNode;
  /** Barra de búsqueda/filtros — típicamente un <Toolbar/> o <FilterBar/>. */
  toolbar?: React.ReactNode;
  /** Muestra el esqueleto de lista mientras carga. */
  isLoading?: boolean;
  /** Estado de error: si hay valor, reemplaza el contenido por un <ErrorState/>. */
  error?: React.ReactNode;
  /** Cuando true, muestra el slot de vacío en lugar de la grilla. */
  isEmpty?: boolean;
  /** Contenido de vacío (default: <EmptyState/> neutro). */
  emptyState?: React.ReactNode;
  /** Tarjetas de la grilla (<EntityInfoCard/>). */
  children?: React.ReactNode;
  /** Paginación opcional al pie — típicamente un <Pagination/>. */
  pagination?: React.ReactNode;
  /** Filas placeholder del esqueleto (default 6). */
  skeletonRows?: number;
  className?: string;
}

/**
 * ListPageScaffold — hoja-lista canónica.
 * data-testid="list-page-scaffold".
 */
export function ListPageScaffold({
  header,
  toolbar,
  isLoading = false,
  error,
  isEmpty = false,
  emptyState,
  children,
  pagination,
  skeletonRows = 6,
  className,
}: ListPageScaffoldProps) {
  let body: React.ReactNode;
  if (error) {
    body =
      typeof error === "boolean" ? (
        <ErrorState message="No se pudo cargar la lista." />
      ) : (
        error
      );
  } else if (isLoading) {
    body = <ListPageSkeleton rows={skeletonRows} data-testid="list-page-scaffold-skeleton" />;
  } else if (isEmpty) {
    body = emptyState ?? <EmptyState title="Sin elementos aún" description="Cuando agregues elementos, aparecerán aquí." />;
  } else {
    body = (
      <div
        data-testid="list-page-scaffold-grid"
        className="grid gap-4"
        style={{ gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))" }}
      >
        {children}
      </div>
    );
  }

  return (
    <PageContainer data-testid="list-page-scaffold" className={cn(className)}>
      <PageContentStack>
        {header}
        {toolbar}
        {body}
        {pagination}
      </PageContentStack>
    </PageContainer>
  );
}

ListPageScaffold.displayName = "ListPageScaffold";
