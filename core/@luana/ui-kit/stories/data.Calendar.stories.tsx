import type { Meta, StoryObj } from "@storybook/nextjs";
import * as React from "react";

import { Calendar } from "../src/calendar";

const meta = {
  title: "Organisms/Calendar",
  component: Calendar,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Calendar` es el selector de fecha base (react-day-picker). Se usa directamente cuando necesitas mostrar un calendario visible sin popover: panel de agenda mensual, selector de fechas en formularios de configuración de eventos. Para la mayoría de los casos en formularios usa `SmartDateTimePicker` que envuelve `Calendar` en un popover con selector de hora incluido.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Formulario de cita con hora** → usa `SmartDateTimePicker` (calendario + hora + zona horaria en un solo componente).",
          "- **Filtro de rango de fechas en un dashboard** → usa `Calendar` en modo `range` (prop `mode=\"range\"`).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Calendar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => {
    const [date, setDate] = React.useState<Date | undefined>(new Date());
    return (
      <Calendar
        mode="single"
        selected={date}
        onSelect={setDate}
        className="rounded-md border"
      />
    );
  },
};

export const Rango: Story = {
  name: "Selección de rango",
  render: () => {
    const [range, setRange] = React.useState<{ from?: Date; to?: Date }>({
      from: new Date(2026, 5, 15),
      to: new Date(2026, 5, 22),
    });
    return (
      <Calendar
        mode="range"
        selected={range as { from: Date; to?: Date } | undefined}
        onSelect={(r) => setRange(r ?? {})}
        className="rounded-md border"
      />
    );
  },
};

export const ConDropdowns: Story = {
  name: "Con dropdowns de mes/año",
  render: () => (
    <Calendar
      mode="single"
      captionLayout="dropdown"
      className="rounded-md border"
    />
  ),
};

export const MultiplesMeses: Story = {
  name: "Dos meses",
  render: () => (
    <Calendar
      mode="single"
      numberOfMonths={2}
      className="rounded-md border"
    />
  ),
};
