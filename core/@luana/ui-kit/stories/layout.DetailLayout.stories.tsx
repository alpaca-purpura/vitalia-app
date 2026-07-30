import type { Meta, StoryObj } from "@storybook/nextjs";

import { DetailLayout, FormLayout } from "../src/layout/layouts";

const meta = {
  title: "Templates/DetailLayout",
  component: DetailLayout,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`DetailLayout` centra y limita el ancho del contenido de detalle a `max-w-3xl` para una línea de lectura cómoda. Úsalo dentro del leaf activo de una hoja-detalle (envuelto por `DetailPageScaffold`).",
          "",
          "`FormLayout` distribuye los campos de un formulario en 1 columna por defecto, o en 2 columnas solo cuando los campos están conceptualmente pareados (`paired={true}`). Úsalo como contenedor de los `<Group>` de un formulario.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** uses `DetailLayout` para listas (la grilla va en `ListPageScaffold` con `auto-fill`).",
          "- **No** uses `FormLayout` con `paired={true}` para cualquier par de campos — solo cuando los dos campos son conceptualmente un par (ej. «Nombre» + «Apellido»).",
          "- Si el contenido es full-width (ej. una tabla o un mapa), puedes omitir `DetailLayout` y gestionar el ancho directamente.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof DetailLayout>;

export default meta;
type Story = StoryObj<typeof meta>;

export const DetailLayoutDefault: Story = {
  name: "DetailLayout (max-w-3xl centrado)",
  args: {
    children: (
      <div className="rounded-lg border border-border/60 bg-card p-6">
        <p className="text-sm text-muted-foreground">
          Contenido de detalle centrado a <code>max-w-3xl</code>. Ancho de lectura
          cómodo para formularios y fichas de entidad.
        </p>
      </div>
    ),
  },
};

export const FormLayoutUnaColumna: Story = {
  name: "FormLayout (1 columna, por defecto)",
  render: () => (
    <FormLayout>
      <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
        Campo A
      </div>
      <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
        Campo B
      </div>
      <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
        Campo C
      </div>
    </FormLayout>
  ),
  parameters: {
    docs: {
      description: {
        story: "1 columna por defecto. Los campos se apilan verticalmente con `gap-6`.",
      },
    },
  },
};

export const FormLayoutDosColumnas: Story = {
  name: "FormLayout paired (2 columnas)",
  render: () => (
    <FormLayout paired>
      <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
        Nombre
      </div>
      <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
        Apellido
      </div>
      <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
        Fecha de nacimiento
      </div>
      <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
        Género
      </div>
    </FormLayout>
  ),
  parameters: {
    docs: {
      description: {
        story:
          "2 columnas solo para campos conceptualmente pareados (ej. Nombre + Apellido). En mobile colapsa a 1 columna (`md:grid-cols-2`).",
      },
    },
  },
};
