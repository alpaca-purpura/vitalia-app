import type { Meta, StoryObj } from "@storybook/nextjs";

import { ListPageSkeleton, FormPageSkeleton } from "../src/layout/skeletons";

const meta = {
  title: "Templates/Skeletons",
  component: ListPageSkeleton,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`ListPageSkeleton` y `FormPageSkeleton` son los **esqueletos de carga canónicos**. Se usan mientras el dato no llegó del servidor para dar al usuario la sensación de que la hoja ya está estructurada (evita el parpadeo de «pantalla en blanco → contenido»).",
          "",
          "Los scaffolds (`ListPageScaffold`, `DetailPageScaffold`, `FormPageScaffold`, `DashboardPageScaffold`) los renderizan automáticamente cuando recibes `isLoading={true}`. Solo necesitarás estos componentes directamente si construís un bloque parcial que tiene su propio estado de carga.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** los uses para el estado vacío de una colección — eso es `<EmptyState>` (los esqueletos son transitorios; el vacío es un estado de datos permanente).",
          "- **No** los uses para el estado de error — eso es `<ErrorState>`.",
          "- Si el bloque es pequeño (ej. una card de métricas), puedes usar `<Skeleton>` atómico directamente.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof ListPageSkeleton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ListaSkeleton: Story = {
  name: "ListPageSkeleton (6 filas)",
  args: {
    rows: 6,
  },
};

export const ListaSkeletonCorta: Story = {
  name: "ListPageSkeleton (3 filas)",
  args: {
    rows: 3,
  },
};

export const FormularioSkeleton: Story = {
  name: "FormPageSkeleton (3 secciones)",
  render: () => <FormPageSkeleton sections={3} />,
  parameters: {
    docs: {
      description: {
        story:
          "`FormPageSkeleton` muestra N secciones de formulario mientras carga. Cada sección tiene un título + 2 campos placeholder.",
      },
    },
  },
};
