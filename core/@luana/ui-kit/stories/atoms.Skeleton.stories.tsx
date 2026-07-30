import type { Meta, StoryObj } from "@storybook/nextjs";

import { Skeleton } from "../src/skeleton";

const meta = {
  title: "Atoms/Skeleton",
  component: Skeleton,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Skeleton` es el placeholder de carga: reemplaza visualmente el contenido mientras los datos están en tránsito. Úsalo en cualquier superficie asíncrona — tarjetas de pacientes, listas de citas, paneles de métricas — para que el usuario perciba que algo está cargando sin un spinner agresivo.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Acciones puntuales (botón enviando)** → usa `LoadingButton` (spinner en el botón, no un skeleton de pantalla).",
          "- **Error en la carga** → reemplaza el skeleton con un `EmptyState` con mensaje de error, no lo dejes visible indefinidamente.",
          "- **Datos que cambian en tiempo real** → un skeleton solo aparece en la carga inicial; usa `refetchInterval` de React Query y no muestra skeleton en refetches posteriores.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Skeleton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => <Skeleton className="h-4 w-48" />,
};

export const TextLines: Story = {
  name: "Líneas de texto",
  render: () => (
    <div className="flex flex-col gap-2 w-72">
      <Skeleton className="h-5 w-full" />
      <Skeleton className="h-5 w-4/5" />
      <Skeleton className="h-5 w-3/5" />
    </div>
  ),
};

export const TarjetaPaciente: Story = {
  name: "Tarjeta de paciente",
  render: () => (
    <div className="flex items-center gap-4 p-4 border rounded-lg w-80">
      <Skeleton className="h-12 w-12 rounded-full" />
      <div className="flex flex-col gap-2 flex-1">
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  ),
};

export const ListaCitas: Story = {
  name: "Lista de citas",
  render: () => (
    <div className="flex flex-col gap-3 w-96">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center gap-3 p-3 border rounded-md">
          <Skeleton className="h-10 w-10 rounded-md" />
          <div className="flex flex-col gap-1.5 flex-1">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
          <Skeleton className="h-6 w-16 rounded-full" />
        </div>
      ))}
    </div>
  ),
};
