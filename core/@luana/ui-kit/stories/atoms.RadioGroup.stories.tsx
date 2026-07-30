import type { Meta, StoryObj } from "@storybook/nextjs";

import { RadioGroup, RadioGroupItem } from "../src/radio-group";
import { Label } from "../src/label";

const meta = {
  title: "Atoms/RadioGroup",
  component: RadioGroup,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`RadioGroup` es para **selección única entre opciones mutuamente excluyentes** visibles todas al mismo tiempo (2–6 ítems). Ej: tipo de turno (presencial / teleconsulta), sexo biológico, modalidad de pago, nivel de urgencia.",
          "",
          "Cada `RadioGroupItem` necesita un `id` y su `Label` con `htmlFor` correspondiente.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Más de 6 opciones** → usa `Select` (despliega sólo las opciones necesarias y ahorra espacio).",
          "- **Selección múltiple** → usa un grupo de `Checkbox`.",
          "- **On/off simple** → usa `Switch`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof RadioGroup>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <RadioGroup defaultValue="presencial">
      <div className="flex items-center gap-2">
        <RadioGroupItem value="presencial" id="r-presencial" />
        <Label htmlFor="r-presencial">Presencial</Label>
      </div>
      <div className="flex items-center gap-2">
        <RadioGroupItem value="teleconsulta" id="r-tele" />
        <Label htmlFor="r-tele">Teleconsulta</Label>
      </div>
      <div className="flex items-center gap-2">
        <RadioGroupItem value="domicilio" id="r-dom" />
        <Label htmlFor="r-dom">A domicilio</Label>
      </div>
    </RadioGroup>
  ),
};

export const Urgencia: Story = {
  name: "Nivel de urgencia",
  render: () => (
    <div className="space-y-2">
      <p className="text-sm font-medium">Prioridad del turno</p>
      <RadioGroup defaultValue="normal">
        {[
          { value: "urgente", label: "Urgente (hoy)" },
          { value: "prioritario", label: "Prioritario (esta semana)" },
          { value: "normal", label: "Normal (próxima disponibilidad)" },
        ].map((o) => (
          <div key={o.value} className="flex items-center gap-2">
            <RadioGroupItem value={o.value} id={`r-${o.value}`} />
            <Label htmlFor={`r-${o.value}`}>{o.label}</Label>
          </div>
        ))}
      </RadioGroup>
    </div>
  ),
};

export const Deshabilitado: Story = {
  name: "Con opción deshabilitada",
  render: () => (
    <RadioGroup defaultValue="standard">
      <div className="flex items-center gap-2">
        <RadioGroupItem value="standard" id="r-std" />
        <Label htmlFor="r-std">Cobertura estándar</Label>
      </div>
      <div className="flex items-center gap-2">
        <RadioGroupItem value="premium" id="r-prem" disabled />
        <Label htmlFor="r-prem" className="opacity-50">
          Cobertura premium (no disponible en tu plan)
        </Label>
      </div>
    </RadioGroup>
  ),
};
