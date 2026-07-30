import type { Meta, StoryObj } from "@storybook/nextjs";
import * as React from "react";

import { TimezoneSelect } from "../src/timezone-select";

const meta = {
  title: "Molecules/TimezoneSelect",
  component: TimezoneSelect,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`TimezoneSelect` es el selector canónico de zona horaria: usa `Intl.supportedValuesOf(\"timeZone\")` para listar todas las zonas IANA con búsqueda en tiempo real. Úsalo en la configuración de la clínica/consultorio, en formularios de evento con fecha y hora, y en la configuración del tenant. Nunca uses un `<select>` nativo (canon §2.5).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **`<select>` nativo** → PROHIBIDO. Usa siempre este componente.",
          "- **Solo mostrar la zona horaria** → texto plano con `formatTenantDate*()`.",
          "- **Selector de moneda** → usa `CurrencySelector`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof TimezoneSelect>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => {
    const [value, setValue] = React.useState("America/Buenos_Aires");
    return (
      <div className="w-80">
        <TimezoneSelect value={value} onValueChange={setValue} />
      </div>
    );
  },
};

export const Mexico: Story = {
  name: "México (America/Mexico_City)",
  render: () => {
    const [value, setValue] = React.useState("America/Mexico_City");
    return (
      <div className="w-80">
        <TimezoneSelect value={value} onValueChange={setValue} />
      </div>
    );
  },
};

export const Colombia: Story = {
  name: "Colombia (America/Bogota)",
  render: () => {
    const [value, setValue] = React.useState("America/Bogota");
    return (
      <div className="w-80">
        <TimezoneSelect value={value} onValueChange={setValue} />
      </div>
    );
  },
};

export const SinSeleccion: Story = {
  name: "Sin selección (placeholder)",
  render: () => {
    const [value, setValue] = React.useState<string | undefined>(undefined);
    return (
      <div className="w-80">
        <TimezoneSelect value={value} onValueChange={setValue} />
      </div>
    );
  },
};
