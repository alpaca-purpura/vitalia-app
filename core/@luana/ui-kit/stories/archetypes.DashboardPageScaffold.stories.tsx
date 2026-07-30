import type { Meta, StoryObj } from "@storybook/nextjs";

import { DashboardPageScaffold } from "../src/archetypes/DashboardPageScaffold";
import { PageHeader, PageSection } from "../src/layout/page";

const header = (
  <PageHeader
    title="Panel de la clínica"
    subtitle="Vista general · Hoy"
  />
);

const meta = {
  title: "Templates/Archetypes/DashboardPageScaffold",
  component: DashboardPageScaffold,
  tags: ["autodocs"],
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es el **scaffold de la hoja-dashboard canónica**. Arma `PageHeader` + un `PageContentStack` de bloques `<PageSection>` + estados (cargando / error).",
          "",
          "Úsalo para hojas que muestran métricas o resúmenes de información divididos en secciones temáticas: panel general de una clínica, resumen del día, métricas de captación.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** lo uses para formularios (eso es `FormPageScaffold`) ni para listas (eso es `ListPageScaffold`).",
          "- **No** lo uses si el dashboard tiene una entidad seleccionable en un panel lateral — ese patrón es `EntityWorkspaceLayout`.",
          "- Si el dashboard solo tiene una sección de contenido sin título, puedes usar `ListPageScaffold` con el toolbar vacío.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof DashboardPageScaffold>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ConSecciones: Story = {
  name: "Con secciones de contenido",
  args: {
    header,
    children: (
      <>
        <PageSection title="Citas de hoy">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {["08:00 — Dra. Fernández", "09:30 — Dr. Rosas", "11:00 — Dra. Herrera"].map(
              (label) => (
                <div
                  key={label}
                  className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground"
                >
                  {label}
                </div>
              ),
            )}
          </div>
        </PageSection>
        <PageSection title="Resumen semanal">
          <div className="rounded-lg border border-border/60 bg-card p-6 text-sm text-muted-foreground">
            Gráfico de citas por día (placeholder).
          </div>
        </PageSection>
        <PageSection title="Doctores disponibles ahora">
          <div className="flex gap-3">
            {["Dra. Vargas", "Dr. Méndez"].map((name) => (
              <div
                key={name}
                className="rounded-full border border-border/60 bg-card px-4 py-1.5 text-sm text-foreground"
              >
                {name}
              </div>
            ))}
          </div>
        </PageSection>
      </>
    ),
  },
};

export const Cargando: Story = {
  args: {
    header,
    isLoading: true,
  },
};

export const ConError: Story = {
  name: "Error de carga",
  args: {
    header,
    error: true,
  },
};
