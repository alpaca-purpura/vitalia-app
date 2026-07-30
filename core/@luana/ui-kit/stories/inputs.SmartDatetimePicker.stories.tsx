import type { Meta, StoryObj } from "@storybook/nextjs";
import * as React from "react";

import { SmartDateTimePicker } from "../src/smart-datetime-picker";

const meta = {
  title: "Molecules/SmartDatetimePicker",
  component: SmartDateTimePicker,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`SmartDateTimePicker` es el selector canónico de fecha + hora con zona horaria: recibe y emite un ISO 8601 UTC, pero muestra la fecha en la zona horaria del tenant (`timezone` prop). Úsalo en formularios de agenda de citas, programación de eventos, inicio de programas. Internamente combina `Calendar` + `Input type=\"time\"` + `date-fns-tz`.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Solo fecha sin hora** → usa `Calendar` directamente.",
          "- **Solo hora** → usa `Input type=\"time\"` directamente.",
          "- **Rango de fechas** → usa `Calendar mode=\"range\"` (sin hora).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof SmartDateTimePicker>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  name: "Buenos Aires",
  render: () => {
    const [value, setValue] = React.useState<string | undefined>(
      "2026-06-22T12:00:00.000Z",
    );
    return (
      <div className="w-72">
        <SmartDateTimePicker
          value={value}
          onChange={setValue}
          timezone="America/Buenos_Aires"
          placeholder="Seleccionar fecha y hora"
        />
        {value && (
          <p className="mt-2 text-xs text-muted-foreground">ISO UTC: {value}</p>
        )}
      </div>
    );
  },
};

export const DateOnly: Story = {
  name: "Solo fecha (showTime=false)",
  render: () => {
    const [value, setValue] = React.useState<string | undefined>(
      "2026-06-22T12:00:00.000Z",
    );
    return (
      <div className="w-72">
        <SmartDateTimePicker
          value={value}
          onChange={setValue}
          timezone="America/Buenos_Aires"
          placeholder="Seleccionar fecha"
          showTime={false}
        />
        {value && (
          <p className="mt-2 text-xs text-muted-foreground">ISO UTC: {value}</p>
        )}
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story:
          "`showTime={false}` oculta la sección de hora y formatea el trigger solo con fecha (`dd/MM/yyyy`). El `onChange` sigue emitiendo un ISO UTC válido (hora interna por defecto 09:00); el consumidor usa solo la parte de fecha. Omitir `showTime` ⇒ comportamiento actual (fecha + hora).",
      },
    },
  },
};

export const DisablePast: Story = {
  name: "Grisar días pasados (disablePast=true)",
  render: () => {
    const [value, setValue] = React.useState<string | undefined>(undefined);
    return (
      <div className="w-72">
        <SmartDateTimePicker
          value={value}
          onChange={setValue}
          timezone="America/Buenos_Aires"
          placeholder="Seleccionar fecha y hora"
          disablePast
        />
        {value && (
          <p className="mt-2 text-xs text-muted-foreground">ISO UTC: {value}</p>
        )}
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story:
          "`disablePast={true}` deshabilita (grisa) los días anteriores a hoy en la zona horaria del tenant (`timezone`). Útil para agendar citas a futuro. Omitir `disablePast` ⇒ comportamiento actual (todos los días seleccionables).",
      },
    },
  },
};

export const Mexico: Story = {
  name: "México",
  render: () => {
    const [value, setValue] = React.useState<string | undefined>(undefined);
    return (
      <div className="w-72">
        <SmartDateTimePicker
          value={value}
          onChange={setValue}
          timezone="America/Mexico_City"
          placeholder="Seleccionar fecha y hora"
        />
        {value && (
          <p className="mt-2 text-xs text-muted-foreground">ISO UTC: {value}</p>
        )}
      </div>
    );
  },
};

export const SinFecha: Story = {
  name: "Sin fecha previa (placeholder)",
  render: () => {
    const [value, setValue] = React.useState<string | undefined>(undefined);
    return (
      <div className="w-72">
        <SmartDateTimePicker
          value={value}
          onChange={setValue}
          timezone="America/Lima"
        />
      </div>
    );
  },
};

/** C2-T4 · consumer story — slot `trigger` ejercido con un trigger compact personalizado. */
export const ConTriggerCustom: Story = {
  name: "Con trigger custom (C2-T4)",
  render: () => {
    const [value, setValue] = React.useState<string | undefined>("2026-06-22T14:30:00.000Z");
    return (
      <div className="flex flex-col gap-3">
        <SmartDateTimePicker
          value={value}
          onChange={setValue}
          timezone="America/Lima"
          trigger={
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-1.5 text-xs font-medium shadow-sm hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              📅 {value ? new Date(value).toLocaleDateString("es-PE") : "Seleccionar"}
            </button>
          }
        />
        {value && (
          <p className="text-xs text-muted-foreground">ISO UTC: {value}</p>
        )}
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story:
          "Slot `trigger` (C2-T4): reemplaza el botón calendario predeterminado con un elemento custom compacto. Radix `PopoverTrigger asChild` clona el elemento y le agrega el handler de apertura. Sin `trigger` → aparece el Button default con `CalendarIcon`.",
      },
    },
  },
};
