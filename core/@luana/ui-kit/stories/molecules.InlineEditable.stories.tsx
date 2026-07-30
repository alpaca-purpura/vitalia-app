import type { Meta, StoryObj } from "@storybook/nextjs";
import * as React from "react";

import {
  InlineEditableInput,
  InlineEditableTextarea,
  type InlineEditableTone,
} from "../src/inline-editable";
import { Label } from "../src/label";

// Use InlineEditableTextarea as the primary component for Meta
const meta = {
  title: "Molecules/InlineEditable",
  component: InlineEditableTextarea,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`InlineEditableTextarea` e `InlineEditableInput` son inputs con chrome invisible en reposo: se leen como texto plano, revelan una affordance al hacer hover y muestran el chrome completo (borde + fondo + foco) al editar. Úsalos en Brand Studio y Offer Studio donde el contenido es lo central y el formulario es secundario (historia de marca, promesa de valor, descripción de oferta).",
          "",
          "- **`InlineEditableTextarea`**: altura automática (`react-textarea-autosize`), mínimo `minRows`. Para textos largos: descripción, historia, narrativa.",
          "- **`InlineEditableInput`**: una línea. Para títulos, nombres, URLs.",
          "- **Tono**: `default` (texto base), `lg` (ligeramente más grande), `xl` (título grande, semi-bold).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Formulario con validación explícita** → usa `Form + FormField + Input/Textarea` (muestra errores Zod claramente).",
          "- **Campo de solo lectura** → texto plano, no `InlineEditable`.",
          "- **Input de búsqueda** → `Input` estándar con `Search` icon.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof InlineEditableTextarea>;

export default meta;
type Story = StoryObj<typeof meta>;

export const DefaultTextarea: Story = {
  name: "Textarea — Historia de marca",
  render: () => {
    const [value, setValue] = React.useState(
      "Vitalia nació de la convicción de que el acceso a salud preventiva de calidad no debe ser un privilegio. Desde 2018, conectamos pacientes con profesionales de primer nivel en toda la región, priorizando la experiencia del paciente en cada paso.",
    );
    return (
      <div className="w-[600px] flex flex-col gap-2">
        <Label className="text-xs text-muted-foreground uppercase tracking-wide">Historia de marca</Label>
        <InlineEditableTextarea
          value={value}
          onChange={setValue}
          tone="default"
          minRows={3}
          placeholder="Escribe la historia de tu marca..."
        />
        <p className="text-xs text-muted-foreground">{value.length} caracteres</p>
      </div>
    );
  },
};

export const DefaultInput: Story = {
  name: "Input — Nombre de marca",
  render: () => {
    const [value, setValue] = React.useState("Vitalia Salud");
    return (
      <div className="w-[400px] flex flex-col gap-2">
        <Label className="text-xs text-muted-foreground uppercase tracking-wide">Nombre de marca</Label>
        <InlineEditableInput
          value={value}
          onChange={setValue}
          tone="xl"
          placeholder="Nombre de tu marca..."
        />
      </div>
    );
  },
};

export const Tonos: Story = {
  name: "Tonos — default / lg / xl",
  render: () => {
    const [values, setValues] = React.useState<Record<InlineEditableTone, string>>({
      default: "Texto en tono default — tamaño base, uso general.",
      lg: "Texto en tono lg — ligeramente más grande.",
      xl: "Título en tono xl",
    });

    const set = (tone: InlineEditableTone) => (v: string) =>
      setValues((prev) => ({ ...prev, [tone]: v }));

    return (
      <div className="w-[560px] flex flex-col gap-6">
        {(["default", "lg", "xl"] as InlineEditableTone[]).map((tone) => (
          <div key={tone} className="flex flex-col gap-1">
            <Label className="text-xs text-muted-foreground uppercase tracking-wide">
              tone=&quot;{tone}&quot;
            </Label>
            <InlineEditableTextarea
              value={values[tone]}
              onChange={set(tone)}
              tone={tone}
              minRows={tone === "xl" ? 1 : 2}
            />
          </div>
        ))}
      </div>
    );
  },
};

export const CampoVacio: Story = {
  name: "Placeholder (campo vacío)",
  render: () => {
    const [titulo, setTitulo] = React.useState("");
    const [descripcion, setDescripcion] = React.useState("");
    return (
      <div className="w-[560px] flex flex-col gap-5">
        <div className="flex flex-col gap-1">
          <Label className="text-xs text-muted-foreground uppercase tracking-wide">Propuesta de valor</Label>
          <InlineEditableInput
            value={titulo}
            onChange={setTitulo}
            tone="xl"
            placeholder="Tu propuesta de valor en una frase..."
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label className="text-xs text-muted-foreground uppercase tracking-wide">Descripción</Label>
          <InlineEditableTextarea
            value={descripcion}
            onChange={setDescripcion}
            minRows={3}
            placeholder="Describe en detalle tu propuesta de valor para el cliente ideal..."
          />
        </div>
      </div>
    );
  },
};
