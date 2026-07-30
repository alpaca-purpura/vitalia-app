import type { Meta, StoryObj } from "@storybook/nextjs";

import { Group, GroupHeader, WhatForChip } from "../src/Group";

const meta = {
  title: "Molecules/Group",
  component: Group,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Group` es el **contenedor canónico de un grupo de campos en un formulario**. Agrupa campos relacionados bajo una cabecera (`GroupHeader`) con título, chip «para qué» opcional, y estado de error semántico (borde rojo + lista de campos faltantes).",
          "",
          "La barrita de color a la izquierda (`accentClass` / `accentVar`) vincula el grupo con un agente específico (ej. Lisa, Adrián) usando tokens — nunca hex hardcodeado.",
          "",
          "`GroupHeader` es la cabecera del grupo. `WhatForChip` es el chip discreto «para qué» con tooltip opcional.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** lo uses como contenedor de página — eso es `PageSection` o el scaffold.",
          "- **No** uses la barrita de color sin un token de agente real (ej. `--agent-lisa`). Si no hay agente asociado, omitís los props de acento.",
          "- **No** pongas un `<FloatingAutosaveIndicator>` dentro de cada `Group` — el indicador flotante es UNO por página, fuera del `Group`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Group>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Basico: Story = {
  args: {
    children: (
      <>
        <GroupHeader title="Datos personales" />
        <div className="grid gap-3">
          <div className="h-9 rounded-md border border-input bg-background" />
          <div className="h-9 rounded-md border border-input bg-background" />
        </div>
      </>
    ),
  },
};

export const ConAccentoDeAgente: Story = {
  name: "Con acento de agente (Lisa)",
  args: {
    accentVar: "--agent-lisa",
    children: (
      <>
        <GroupHeader
          title="Identidad de marca"
          whatFor="Para Lisa"
          whatForTooltip="Lisa usa estos datos para personalizar las respuestas al paciente."
        />
        <div className="grid gap-3">
          <div className="h-9 rounded-md border border-input bg-background" />
          <div className="h-9 rounded-md border border-input bg-background" />
        </div>
      </>
    ),
  },
};

export const ConErrorSemantico: Story = {
  name: "Con error semántico (campos faltantes)",
  args: {
    hasError: true,
    children: (
      <>
        <GroupHeader
          title="Datos profesionales"
          missingFields={["Especialidad", "Número de matrícula"]}
        />
        <div className="grid gap-3">
          <div className="h-9 rounded-md border border-destructive/50 bg-background" />
          <div className="h-9 rounded-md border border-input bg-background" />
        </div>
      </>
    ),
  },
};

export const WhatForChipSolo: Story = {
  name: "WhatForChip (chip «para qué»)",
  render: () => (
    <div className="flex flex-col gap-4">
      <WhatForChip label="Para Lisa" />
      <WhatForChip
        label="Para la agenda"
        tooltip="Adrián usa estos datos para optimizar la disponibilidad de turnos."
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          "`WhatForChip` es brand-agnostic: el consumer decide el texto. Pasa `tooltip` para agregar contexto al hover.",
      },
    },
  },
};
