import type { Meta, StoryObj } from "@storybook/nextjs";
import * as React from "react";

import { TimePicker } from "../src/TimePicker";

const meta = {
  title: "Molecules/TimePicker",
  component: TimePicker,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`TimePicker` selecciona **una hora** (HH:mm 24h) con un campo **segmentado tokenizado** — reemplaza el chrome del `<input type=\"time\"`> nativo (inconsistente cross-navegador). **Híbrido teclado + mouse:** se escribe con auto-avance (`↑↓` por segmento, `←→` para moverse) **o** se hace click en el chevron `▾` para abrir un **dropdown** con columnas Hora (00–23) y Min (`minuteOptions`, default 00/10/20/30/40/50) — el mouse-only no necesita teclado, y el teclado igual permite un minuto fuera de lista (ej. 31). Úsalo para hora de inicio de un evento, recordatorio, corte.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Rango horario (inicio–fin)** → usa `TimeRangePicker` (compone dos de estos).",
          "- **Fecha + hora** → usa `SmartDateTimePicker`.",
          "- **Solo fecha** → usa `Calendar`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof TimePicker>;

export default meta;
type Story = StoryObj<typeof meta>;

function Controlled({ initial }: { initial?: string }) {
  const [value, setValue] = React.useState(initial ?? "");
  return (
    <div className="flex flex-col items-start gap-3">
      <TimePicker value={value} onChange={setValue} />
      <p className="font-mono text-xs text-muted-foreground">{value || "—"}</p>
    </div>
  );
}

export const Default: Story = {
  render: () => <Controlled />,
};

export const ConValor: Story = {
  name: "Con valor",
  render: () => <Controlled initial="14:30" />,
};

export const Deshabilitado: Story = {
  render: () => <TimePicker value="09:00" onChange={() => {}} disabled />,
};
