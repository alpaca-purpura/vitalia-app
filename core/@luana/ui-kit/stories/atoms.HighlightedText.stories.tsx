import type { Meta, StoryObj } from "@storybook/nextjs";

import { HighlightedText } from "../src/highlighted-text";

const meta = {
  title: "Atoms/HighlightedText",
  component: HighlightedText,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`HighlightedText` resalta las ocurrencias de un término de búsqueda dentro de un texto. Úsalo en resultados de búsqueda de pacientes, doctores, servicios o cualquier lista filtrable donde el usuario necesita ver por qué un resultado coincide con su query.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Sin query activa** → el componente pasa el texto sin marcar; no necesitas condicionar su uso.",
          "- **Resaltar semánticamente (error, advertencia)** → usa `Badge` o colores de texto directos (`text-destructive`).",
          "- **Texto enriquecido estructurado** → usa Markdown o un parser dedicado.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof HighlightedText>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <HighlightedText text="Dra. Valentina Suárez — Cardiología" query="cardio" />
  ),
};

export const SinCoincidencia: Story = {
  name: "Sin coincidencia",
  render: () => (
    <HighlightedText text="Dr. Marcos Ávila — Neurología" query="cardio" />
  ),
};

export const ListaBusqueda: Story = {
  name: "Lista de resultados de búsqueda",
  render: () => {
    const doctors = [
      "Dra. Valentina Suárez — Cardiología",
      "Dr. Andrés Medina — Medicina General",
      "Dra. Camila Torres — Nutrición y Metabolismo",
      "Dr. Rodrigo Fuentes — Cardiología Intervencionista",
      "Lic. Andrea Rojas — Psicología Clínica",
    ];
    const query = "card";
    return (
      <ul className="flex flex-col gap-2 w-96">
        {doctors.map((doc) => (
          <li key={doc} className="px-3 py-2 rounded-md border text-sm">
            <HighlightedText text={doc} query={query} />
          </li>
        ))}
      </ul>
    );
  },
};

export const QueryVacia: Story = {
  name: "Query vacía (sin resaltar)",
  render: () => (
    <HighlightedText text="Dra. Valentina Suárez — Cardiología" query="" />
  ),
};
