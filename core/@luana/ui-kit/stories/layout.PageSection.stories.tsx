import type { Meta, StoryObj } from "@storybook/nextjs";

import { PageSection } from "../src/layout/page";

const meta = {
  title: "Templates/PageSection",
  component: PageSection,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es una **sección semántica con título `h2` opcional**. Úsala para dividir el contenido de una hoja en bloques temáticos bien delimitados (ej. «Datos personales» / «Horarios» / «Estadísticas recientes»).",
          "",
          "Cuando tiene título, el `section` lleva `aria-labelledby` automáticamente para que los lectores de pantalla puedan navegar entre secciones.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** la uses para el encabezado principal de la hoja — eso es `<PageHeader>` (con `h1`).",
          "- **No** la uses para el agrupamiento de campos en un formulario — ahí corresponde `<Group>` (con barrita de agente y estado de error).",
          "- **No** la anides dentro de otra `<PageSection>` — para sub-bloques usa directamente `<div>` semántico o `<Group>`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof PageSection>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ConTitulo: Story = {
  args: {
    title: "Próximas citas",
    children: (
      <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
        Lista de citas (contenido de la sección).
      </div>
    ),
  },
};

export const SinTitulo: Story = {
  args: {
    children: (
      <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
        Bloque sin título de sección.
      </div>
    ),
  },
};

export const VariasSecciones: Story = {
  name: "Varias secciones en una hoja",
  render: () => (
    <div className="flex flex-col gap-6 p-6">
      <PageSection title="Datos del paciente">
        <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
          Nombre, edad, documento, contacto…
        </div>
      </PageSection>
      <PageSection title="Historial de consultas">
        <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
          Últimas 5 consultas…
        </div>
      </PageSection>
      <PageSection title="Medicación activa">
        <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
          Medicamentos en curso…
        </div>
      </PageSection>
    </div>
  ),
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        story: "Varias secciones apiladas. El espaciado lo da el `gap-6` del contenedor padre.",
      },
    },
  },
};
