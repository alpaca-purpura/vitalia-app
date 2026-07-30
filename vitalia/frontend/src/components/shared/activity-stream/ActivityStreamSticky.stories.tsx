// cap: agentic.lucas-daily-analysis
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { ActivityStreamSticky } from "./ActivityStreamSticky";
import type { ActivityItem } from "./ActivityStreamSticky";

/**
 * ActivityStreamSticky — collapsible activity stream panel.
 * 32px collapsed / 240px expanded. Uses fake activity data.
 */
const meta: Meta<typeof ActivityStreamSticky> = {
  title: "Shared/ActivityStreamSticky",
  component: ActivityStreamSticky,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
  },
};
export default meta;

type Story = StoryObj<typeof ActivityStreamSticky>;

const fewItems: ActivityItem[] = [
  {
    id: "act-1",
    type: "agent",
    agentRole: "valeria",
    action: "actualizó el estado",
    target: "del paciente",
    timestamp: "hace 5 min",
  },
  {
    id: "act-2",
    type: "user",
    userName: "Dr. García",
    action: "revisó el historial",
    timestamp: "hace 15 min",
  },
];

const manyItems: ActivityItem[] = [
  {
    id: "m1",
    type: "agent",
    agentRole: "valeria",
    action: "envió recordatorio de cita",
    timestamp: "hace 2 min",
  },
  {
    id: "m2",
    type: "agent",
    agentRole: "lucas",
    action: "generó recomendación de etapa",
    timestamp: "hace 8 min",
  },
  {
    id: "m3",
    type: "user",
    userName: "Dra. Pérez",
    action: "aprobó tratamiento",
    timestamp: "hace 22 min",
  },
  {
    id: "m4",
    type: "agent",
    agentRole: "adrian",
    action: "procesó pago del depósito",
    timestamp: "hace 35 min",
  },
  {
    id: "m5",
    type: "user",
    userName: "Recep. Ana",
    action: "registró nueva cita",
    timestamp: "hace 1 h",
  },
  {
    id: "m6",
    type: "agent",
    agentRole: "valeria",
    action: "actualizó el perfil del contacto",
    timestamp: "hace 2 h",
  },
];

/** Empty state */
export const EmptyState: Story = {
  name: "Estado vacío",
  args: { items: [] },
};

/** Loading state */
export const LoadingState: Story = {
  name: "Cargando",
  args: { items: [], isLoading: true },
};

/** Few events — 2 items */
export const FewEvents: Story = {
  name: "Pocos eventos (2)",
  args: { items: fewItems },
};

/** Many events — 6 items (tests scroll) */
export const ManyEvents: Story = {
  name: "Muchos eventos (6 — scroll interno)",
  args: { items: manyItems },
};

/** Collapsed by default */
export const CollapsedDefault: Story = {
  name: "Colapsado por defecto",
  args: {
    items: fewItems,
  },
};
