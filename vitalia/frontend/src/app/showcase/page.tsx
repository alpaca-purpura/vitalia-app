// canon: design-system-canon.md §5 · story-origin: core-ds-foundation
"use client";

/**
 * /showcase — Catálogo vivo del design-system @luana/ui-kit (R-FID durable showcase).
 *
 * Renderiza los componentes REALES de @luana/ui-kit (no la showcase.html estática)
 * agrupados por categoría, con datos LatAm realistas (español neutro). Ruta pública
 * (catálogo de diseño · sin tenant · sin PHI) — ver proxy.ts isPublicRoute.
 *
 * Cada sección vive en ./sections/* y se compone de las primitivas del kit.
 */

import { PageContainer, PageContentStack, PageHeader } from "@luana/ui-kit";

import { AtomsSection } from "./sections/AtomsSection";
import { LayoutPrimitivesSection } from "./sections/LayoutPrimitivesSection";
import { EntitySection } from "./sections/EntitySection";
import { AutosaveGroupSection } from "./sections/AutosaveGroupSection";
import { ArchetypesSection } from "./sections/ArchetypesSection";

export default function ShowcasePage() {
  return (
    <main className="min-h-screen bg-background">
      <PageContainer>
        <PageContentStack>
          <PageHeader
            title="Design System · @luana/ui-kit"
            subtitle="Catálogo vivo de los componentes reales del canon. Datos de ejemplo LatAm."
          />
          <AtomsSection />
          <LayoutPrimitivesSection />
          <EntitySection />
          <AutosaveGroupSection />
          <ArchetypesSection />
        </PageContentStack>
      </PageContainer>
    </main>
  );
}
