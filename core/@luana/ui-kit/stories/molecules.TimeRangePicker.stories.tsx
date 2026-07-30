import type { Meta, StoryObj } from "@storybook/nextjs";
import * as React from "react";

import { TimeRangePicker, type TimeRange } from "../src/TimeRangePicker";

const meta = {
  title: "Molecules/TimeRangePicker",
  component: TimeRangePicker,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`TimeRangePicker` selecciona un **rango horario (inicio–fin)** dentro de un día: horario de atención, ventanas de disponibilidad, franjas de campaña. Compone dos `TimePicker` segmentados (tokenizados, `↑↓` por segmento — NO `<input type=time>` nativo) + **presets** de acceso rápido (Mañana/Tarde/Todo el día, overridables vía `presets`) + valida que el inicio sea anterior al fin (`aria-invalid` + mensaje `role=\"alert\"`).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Un solo instante (fecha + hora)** → usa `SmartDateTimePicker`.",
          "- **Solo una hora** → usa `Input type=\"time\"` directamente.",
          "- **Rango de FECHAS** → usa `Calendar mode=\"range\"`.",
          "- **Slots de disponibilidad con bloques ocupado/libre** → es un timeline de dominio (vitalia `DayAvailabilityStrip`), no este picker.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof TimeRangePicker>;

export default meta;
type Story = StoryObj<typeof meta>;

function Controlled({ initial }: { initial?: Partial<TimeRange> }) {
  const [range, setRange] = React.useState<Partial<TimeRange>>(initial ?? {});
  return (
    <div className="w-80">
      <TimeRangePicker value={range} onChange={setRange} />
      <p className="mt-3 font-mono text-xs text-muted-foreground">
        {range.start || "—"} → {range.end || "—"}
      </p>
    </div>
  );
}

export const Default: Story = {
  render: () => <Controlled />,
};

export const ConValores: Story = {
  name: "Con valores (horario de atención)",
  render: () => <Controlled initial={{ start: "09:00", end: "18:00" }} />,
};

export const Invalido: Story = {
  name: "Inválido (inicio ≥ fin)",
  render: () => <Controlled initial={{ start: "18:00", end: "09:00" }} />,
};

export const SinPresets: Story = {
  name: "Sin presets",
  render: () => {
    const [range, setRange] = React.useState<Partial<TimeRange>>({ start: "10:00", end: "12:00" });
    return (
      <div className="w-80">
        <TimeRangePicker value={range} onChange={setRange} presets={[]} />
      </div>
    );
  },
};

export const Deshabilitado: Story = {
  render: () => (
    <div className="w-80">
      <TimeRangePicker value={{ start: "09:00", end: "18:00" }} onChange={() => {}} disabled />
    </div>
  ),
};
