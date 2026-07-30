import type { Meta, StoryObj } from "@storybook/nextjs";

import { Checkbox } from "../src/checkbox";
import { Label } from "../src/label";

const meta = {
  title: "Atoms/Checkbox",
  component: Checkbox,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Checkbox` es para **selección múltiple independiente**: el usuario puede activar o desactivar cada opción sin afectar las demás. Ideal para filtros, permisos, aceptar términos, seleccionar días de disponibilidad.",
          "",
          "Siempre acompáñalo de un `Label` con `htmlFor` para accesibilidad. Para grupos de opciones mutuamente excluyentes usa `RadioGroup` en su lugar.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Opciones mutuamente excluyentes** → usa `RadioGroup`.",
          "- **Activar/desactivar UNA sola configuración** → usa `Switch` (semánticamente es on/off, no selección múltiple).",
          "- **Seleccionar ítems de una lista larga** → considera una `DataTable` con selección de filas.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Checkbox>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Checkbox id="consent" />
      <Label htmlFor="consent">
        El paciente dio su consentimiento informado
      </Label>
    </div>
  ),
};

export const Marcado: Story = {
  name: "Marcado por defecto",
  render: () => (
    <div className="flex items-center gap-2">
      <Checkbox id="reminder" defaultChecked />
      <Label htmlFor="reminder">Enviar recordatorio por WhatsApp</Label>
    </div>
  ),
};

export const Deshabilitado: Story = {
  name: "Deshabilitado",
  render: () => (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <Checkbox id="disabled-unchecked" disabled />
        <Label htmlFor="disabled-unchecked" className="opacity-50">
          Opción no disponible
        </Label>
      </div>
      <div className="flex items-center gap-2">
        <Checkbox id="disabled-checked" disabled defaultChecked />
        <Label htmlFor="disabled-checked" className="opacity-50">
          Activado (solo lectura)
        </Label>
      </div>
    </div>
  ),
};

export const Grupo: Story = {
  name: "Grupo de checkboxes",
  render: () => (
    <div className="flex flex-col gap-2">
      <p className="text-sm font-medium">Canales de contacto</p>
      {[
        { id: "whatsapp", label: "WhatsApp" },
        { id: "email", label: "Correo electrónico" },
        { id: "sms", label: "SMS" },
        { id: "phone", label: "Llamada telefónica" },
      ].map((ch) => (
        <div key={ch.id} className="flex items-center gap-2">
          <Checkbox id={ch.id} defaultChecked={ch.id === "whatsapp" || ch.id === "email"} />
          <Label htmlFor={ch.id}>{ch.label}</Label>
        </div>
      ))}
    </div>
  ),
};
