import type { Meta, StoryObj } from "@storybook/nextjs";

import { FormActionBar } from "../src/FormActionBar";

const meta = {
  title: "Organisms/FormActionBar",
  component: FormActionBar,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es la **barra sticky de envío explícito** — el *segundo modo* del canon de formularios. El canon por defecto es **autosave** (`FloatingAutosaveIndicator` + `use-autosave`, sin botón de guardado). `FormActionBar` es el modo **deliberado**: crear/enviar un registro nuevo con un submit confirmado (ej. «Nueva cita»). El usuario completa, ve el `hint` del estado, y confirma con el botón primario.",
          "",
          "Queda pegada al fondo (`sticky bottom-0`) con borde superior + sombra hacia arriba y superficie `bg-card` — mismo lenguaje que la franja N3 invertida. El botón primario puede teñirse con el color del agente dueño de la hoja vía `accent` (token, nunca hex).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Edición de una entidad existente** → autosave (`FloatingAutosaveIndicator`), sin botón de guardar.",
          "- **Acción destructiva con confirmación** → `AlertDialog`, no una barra de envío.",
          "- **Wizard multi-paso** → la barra puede servir, pero el control de pasos (Atrás/Siguiente) lo maneja el wizard.",
        ].join("\n"),
      },
    },
  },
  args: {
    submitLabel: "Crear cita",
    cancelLabel: "Cancelar",
    hint: "Sin guardar todavía",
  },
} satisfies Meta<typeof FormActionBar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    onCancel: () => {},
    onSubmit: () => {},
  },
};

export const Enviando: Story = {
  name: "Enviando (submitting)",
  args: {
    submitting: true,
    hint: "Creando la cita…",
    onCancel: () => {},
    onSubmit: () => {},
  },
  parameters: {
    docs: {
      description: {
        story:
          "Con `submitting` el botón primario se deshabilita y muestra un spinner; el botón cancelar también se bloquea para evitar abandonar a mitad del envío.",
      },
    },
  },
};

export const Bloqueado: Story = {
  name: "Bloqueado por validación (submitDisabled)",
  args: {
    submitDisabled: true,
    hint: "Completa los campos obligatorios",
    onCancel: () => {},
    onSubmit: () => {},
  },
  parameters: {
    docs: {
      description: {
        story:
          "`submitDisabled` deshabilita el envío mientras la validación no pasa (sin spinner — no hay nada en curso).",
      },
    },
  },
};

export const ConAcento: Story = {
  name: "Con color de agente (accent)",
  args: {
    accent: "mateo",
    submitLabel: "Crear cita",
    hint: "Agenda de Mateo",
    onCancel: () => {},
    onSubmit: () => {},
  },
  parameters: {
    docs: {
      description: {
        story:
          "El botón primario toma el color del agente dueño de la hoja vía `accent` (clave del agente → `hsl(var(--agent-{accent}))`, token-driven, nunca hex). Acá Mateo (ámbar).",
      },
    },
  },
};
