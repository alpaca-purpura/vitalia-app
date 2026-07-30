// canon: design-system-canon.md §6.2 · story-origin: core-ds-foundation
"use client";

/**
 * FormPageScaffold.tsx — Archetype "formulario" (canon §6.2 · @luana/ui-kit).
 *
 * SCAFFOLD: arma PageHeader + FormLayout (1-col por defecto, 2-col solo para
 * campos pareados) + el slot del indicador de autoguardado flotante (UNA sola
 * instancia por página, canon §2.6) + esqueleto de carga.
 *
 * Slots:
 *   - `header`            → un <PageHeader/>
 *   - `children`          → grupos de campos (<Group/>) dentro del <FormLayout/>
 *   - `autosaveIndicator` → un <FloatingAutosaveIndicator/> (último hijo, sticky)
 *
 * Estado: loading → contenido. Los errores de formulario son por-campo/grupo
 * (no un estado de página completa).
 *
 * Named export (NO default).
 */

import * as React from "react";

import { cn } from "@luana/format/utils";

import { PageContainer, PageContentStack } from "../layout/page";
import { FormLayout } from "../layout/layouts";
import { FormPageSkeleton } from "../layout/skeletons";

export interface FormPageScaffoldProps {
  /** Encabezado de la hoja — típicamente un <PageHeader/>. */
  header: React.ReactNode;
  /** 2 columnas SOLO cuando los campos están conceptualmente pareados (canon §2.7). */
  paired?: boolean;
  /** Muestra el esqueleto de formulario mientras carga. */
  isLoading?: boolean;
  /** Grupos de campos del formulario (<Group/>). */
  children?: React.ReactNode;
  /**
   * Indicador de autoguardado flotante — UNA sola instancia por página (canon §2.6).
   * Se ancla como último hijo del contenedor scrolleable.
   */
  autosaveIndicator?: React.ReactNode;
  /** Secciones placeholder del esqueleto (default 3). */
  skeletonSections?: number;
  className?: string;
}

/**
 * FormPageScaffold — hoja-formulario canónica.
 * data-testid="form-page-scaffold".
 */
export function FormPageScaffold({
  header,
  paired = false,
  isLoading = false,
  children,
  autosaveIndicator,
  skeletonSections = 3,
  className,
}: FormPageScaffoldProps) {
  return (
    <PageContainer data-testid="form-page-scaffold" className={cn(className)}>
      <PageContentStack>
        {header}
        {isLoading ? (
          <FormPageSkeleton sections={skeletonSections} data-testid="form-page-scaffold-skeleton" />
        ) : (
          <FormLayout paired={paired}>{children}</FormLayout>
        )}
        {/* Indicador de autoguardado — último hijo, sticky bottom-center (canon §2.6). */}
        {autosaveIndicator}
      </PageContentStack>
    </PageContainer>
  );
}

FormPageScaffold.displayName = "FormPageScaffold";
