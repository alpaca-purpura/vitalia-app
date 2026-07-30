import type { Meta, StoryObj } from "@storybook/nextjs";

import { Progress } from "../src/progress";

const meta = {
  title: "Atoms/Progress",
  component: Progress,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Progress` muestra el avance cuantificable de un proceso con valor entre 0 y 100: completitud del perfil de marca, progreso de onboarding, porcentaje de campos completados en una sección. El valor se pasa via `value` (número).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Carga indeterminada** → usa `Skeleton` (el proceso no tiene porcentaje conocido).",
          "- **Pasos de un wizard** → usa `Steps` o `Stepper` con pasos discretos, no una barra continua.",
          "- **Botón enviando** → usa `LoadingButton` con spinner.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Progress>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => <Progress value={60} className="w-72" />,
};

export const Vacio: Story = {
  name: "Sin progreso",
  render: () => <Progress value={0} className="w-72" />,
};

export const Completo: Story = {
  name: "Completado (100%)",
  render: () => <Progress value={100} className="w-72" />,
};

export const PerfilMarca: Story = {
  name: "Completitud del perfil",
  render: () => (
    <div className="flex flex-col gap-3 w-80">
      {[
        { label: "Identidad de marca", value: 100 },
        { label: "Posicionamiento", value: 75 },
        { label: "Buyer persona", value: 40 },
        { label: "Voz y tono", value: 20 },
      ].map((item) => (
        <div key={item.label} className="flex flex-col gap-1">
          <div className="flex justify-between text-sm">
            <span>{item.label}</span>
            <span className="text-muted-foreground">{item.value}%</span>
          </div>
          <Progress value={item.value} className="h-2" />
        </div>
      ))}
    </div>
  ),
};
