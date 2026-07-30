import type { Meta, StoryObj } from "@storybook/nextjs";

import { Textarea } from "../src/textarea";

const meta = {
  title: "Atoms/Textarea",
  component: Textarea,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Textarea` es el campo de texto multilínea del design system. Úsalo para contenido extenso: notas clínicas, descripción del servicio, instrucciones post-consulta, motivo de consulta.",
          "",
          "Siempre acompáñalo de un `Label` accesible y, para formularios de muchos campos, considera el autosave automático del form-runtime (el usuario no debe perder texto no guardado).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- Para texto corto de una línea → usa `Input`.",
          "- Para listas de ítems editables (ej. síntomas) → usa el pattern array de form-runtime (`cards` o `split`) en lugar de un textarea simulando lista.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Textarea>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    placeholder: "Notas clínicas del paciente...",
    id: "clinical-notes",
    rows: 4,
  },
};

export const ConValor: Story = {
  name: "Con contenido",
  args: {
    defaultValue:
      "Paciente refiere dolor en zona lumbar de intensidad 6/10. Sin irradiación hacia miembros inferiores. Se indica reposo relativo y AINE por 5 días.",
    id: "clinical-notes-filled",
    rows: 5,
  },
};

export const Deshabilitado: Story = {
  name: "Deshabilitado",
  args: {
    defaultValue: "Contenido de solo lectura.",
    disabled: true,
    id: "readonly-notes",
  },
};
