import type { Meta, StoryObj } from "@storybook/nextjs";
import * as React from "react";

import { CurrencySelector } from "../src/currency-selector";

const meta = {
  title: "Molecules/CurrencySelector",
  component: CurrencySelector,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`CurrencySelector` es el selector canónico de moneda: reemplaza cualquier `<select>` nativo o `Select` básico para seleccionar monedas. Combina Combobox + Popover con búsqueda en tiempo real, muestra bandera + código ISO + nombre completo. Úsalo en configuración del tenant, formularios de precio de ofertas, y ajustes de facturación.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **`<select>` nativo** → PROHIBIDO en el design system (canon §2.5). Usa siempre este componente.",
          "- **Solo mostrar el código de moneda como texto** → usa `Badge` o texto plano; no necesitas el selector.",
          "- **Zona horaria** → usa `TimezoneSelect` (mismo patrón Combobox, distinto dominio).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof CurrencySelector>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => {
    const [value, setValue] = React.useState("ARS");
    return (
      <div className="w-72">
        <CurrencySelector value={value} onValueChange={setValue} />
      </div>
    );
  },
};

export const MXN: Story = {
  name: "Moneda México (MXN)",
  render: () => {
    const [value, setValue] = React.useState("MXN");
    return (
      <div className="w-72">
        <CurrencySelector value={value} onValueChange={setValue} />
      </div>
    );
  },
};

export const COP: Story = {
  name: "Moneda Colombia (COP)",
  render: () => {
    const [value, setValue] = React.useState("COP");
    return (
      <div className="w-72">
        <CurrencySelector value={value} onValueChange={setValue} />
      </div>
    );
  },
};

export const SinSeleccion: Story = {
  name: "Sin selección previa",
  render: () => {
    const [value, setValue] = React.useState("");
    return (
      <div className="w-72">
        <CurrencySelector value={value} onValueChange={setValue} />
      </div>
    );
  },
};
