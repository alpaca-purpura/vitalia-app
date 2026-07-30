import type { Meta, StoryObj } from "@storybook/nextjs";

import { PlaceholderCard } from "../src";

/**
 * Story consumes the REAL PlaceholderCard from src/. Presentational card with
 * icon + heading + description + StatusDot (+ optional count). Brand-agnostic.
 */
const meta = {
  title: "Shell/PlaceholderCard",
  component: PlaceholderCard,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`PlaceholderCard` es una tarjeta liviana para **poblar una sub-tab/sección que todavía no tiene su UI final**: ícono + título + descripción/stat + punto de estado. Útil para los empty/placeholder de las pantallas del shell mientras se construye la funcionalidad real.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Una entidad real de negocio** (clickeable, con kebab) → `EntityInfoCard`.",
          "- **Estado vacío de una hoja** → `EmptyState` (page-primitive).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof PlaceholderCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  name: "Tarjeta de placeholder",
  args: {
    icon: "📅",
    title: "Agenda de hoy",
    description: "8 turnos confirmados · 2 pendientes",
    status: "green",
    count: 10,
  },
};

export const Grilla: Story = {
  name: "Grilla de placeholders",
  render: () => (
    <div className="grid w-[640px] max-w-full grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-3">
      <PlaceholderCard icon="📅" title="Agenda" description="8 turnos hoy" status="green" count={8} />
      <PlaceholderCard icon="🧲" title="Leads" description="3 nuevos sin contactar" status="yellow" count={3} />
      <PlaceholderCard icon="💬" title="Conversaciones" description="Sin pendientes" status="gray" />
      <PlaceholderCard icon="📣" title="Campañas" description="1 activa" status="green" count={1} />
    </div>
  ),
};
