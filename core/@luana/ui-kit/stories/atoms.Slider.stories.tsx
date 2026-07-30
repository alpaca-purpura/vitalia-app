import type { Meta, StoryObj } from "@storybook/nextjs";

import { Slider } from "../src/slider";

const meta = {
  title: "Atoms/Slider",
  component: Slider,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Slider` es para parámetros numéricos continuos dentro de un rango conocido: ajustar la energía o el calor de la personalidad del agente (0-1), configurar un umbral de confianza, definir un rango de precios en un filtro. Ofrece retroalimentación visual inmediata del valor.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Valor exacto requerido** → usa `Input type=\"number\"` (el slider es difícil de controlar con precisión).",
          "- **Lista de opciones discretas** → usa `Select` o `RadioGroup` (no un slider de pasos).",
          "- **Rango de precio en forma** → un slider de doble extremo es correcto; revisa si el design system ya tiene esa variante antes de construirla.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Slider>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => <Slider defaultValue={[50]} max={100} step={1} className="w-72" />,
};

export const Rango: Story = {
  name: "Rango doble",
  render: () => (
    <Slider defaultValue={[25, 75]} max={100} step={5} className="w-72" />
  ),
};

export const PersonalidadAgente: Story = {
  name: "Personalidad del agente",
  render: () => (
    <div className="flex flex-col gap-5 w-80">
      {[
        { label: "Energía", defaultValue: [65] },
        { label: "Calidez", defaultValue: [80] },
        { label: "Humor", defaultValue: [30] },
        { label: "Expresividad", defaultValue: [55] },
      ].map((dim) => (
        <div key={dim.label} className="flex flex-col gap-2">
          <div className="flex justify-between text-sm">
            <span>{dim.label}</span>
            <span className="text-muted-foreground">{dim.defaultValue[0]}%</span>
          </div>
          <Slider defaultValue={dim.defaultValue} max={100} step={5} />
        </div>
      ))}
    </div>
  ),
};

export const Deshabilitado: Story = {
  name: "Deshabilitado",
  render: () => <Slider defaultValue={[40]} max={100} disabled className="w-72" />,
};
