import type { Meta, StoryObj } from "@storybook/nextjs";

import { Label } from "../src/label";
import { Input } from "../src/input";

const meta = {
  title: "Atoms/Label",
  component: Label,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Label` es la etiqueta accesible de un campo de formulario. Siempre lo usás junto a `Input`, `Textarea`, `Checkbox`, `Switch` o `RadioGroup` con el par `htmlFor` ↔ `id`. Esto permite al usuario hacer clic en la etiqueta para enfocar el campo y garantiza que los lectores de pantalla anuncien el campo correctamente.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** lo uses como título de sección → usa `<h3>` o `GroupHeader`.",
          "- **No** omitas el `Label` y uses `placeholder` como única etiqueta: el placeholder desaparece al escribir y no es suficiente para accesibilidad.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Label>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: "Especialidad médica",
    htmlFor: "specialty",
  },
};

export const ConCampo: Story = {
  name: "Label vinculado a Input",
  render: () => (
    <div className="grid gap-1.5">
      <Label htmlFor="email">Correo del paciente</Label>
      <Input type="email" id="email" placeholder="correo@ejemplo.com" className="w-72" />
    </div>
  ),
};

export const Requerido: Story = {
  name: "Campo requerido (asterisco semántico)",
  render: () => (
    <div className="grid gap-1.5">
      <Label htmlFor="name">
        Nombre completo <span className="text-destructive">*</span>
      </Label>
      <Input id="name" placeholder="Ingresa el nombre" className="w-72" />
    </div>
  ),
};
