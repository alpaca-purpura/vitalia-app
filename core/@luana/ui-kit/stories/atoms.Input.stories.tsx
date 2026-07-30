import type { Meta, StoryObj } from "@storybook/nextjs";

import { Input } from "../src/input";

const meta = {
  title: "Atoms/Input",
  component: Input,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Input` es el campo de texto de una línea del design system. Úsalo para capturar valores cortos: nombre del paciente, email, teléfono, número de matrícula, precio.",
          "",
          "Siempre acompáñalo de un `Label` accesible (`htmlFor` ↔ `id`) y, cuando aplique, de un mensaje de error con `role='alert'`.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- Para texto largo (descripción, notas clínicas) → usa `Textarea`.",
          "- Para búsqueda global con historial y atajos → usa el patrón `Command`.",
          "- Para selección en un conjunto cerrado → usa `Select` canónico.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    placeholder: "Nombre del paciente",
    id: "patient-name",
  },
};

export const ConValor: Story = {
  name: "Con valor",
  args: {
    defaultValue: "Valentina Suárez",
    id: "patient-name-filled",
  },
};

export const Deshabilitado: Story = {
  name: "Deshabilitado",
  args: {
    defaultValue: "PROF-0048",
    disabled: true,
    id: "prof-id",
  },
};

export const Email: Story = {
  args: {
    type: "email",
    placeholder: "correo@clinica.com",
    id: "email-input",
  },
};

export const Numero: Story = {
  name: "Tipo número",
  args: {
    type: "number",
    placeholder: "Duración (minutos)",
    min: 15,
    step: 15,
    id: "duration-input",
  },
};
