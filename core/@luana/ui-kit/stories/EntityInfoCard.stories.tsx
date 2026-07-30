import type { Meta, StoryObj } from "@storybook/nextjs";
import * as React from "react";
import { Stethoscope } from "lucide-react";

import {
  EntityInfoCard,
  EntityInfoCardSkeleton,
  EntityInfoCardEmpty,
} from "../src/EntityInfoCard";

/**
 * Story consumes the REAL EntityInfoCard from src/ — never a copy.
 * Data is realistic LatAm clinic content (doctors), Spanish neutro.
 */
const meta = {
  title: "Organisms/EntityInfoCard",
  component: EntityInfoCard,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es la **tarjeta de entidad** del modo *master* de una vista lista/detalle (canon §2.3, Opción B). Úsala para cada ítem de una grilla `auto-fill minmax(250px, 1fr)`: doctores, pacientes, servicios, campañas, leads — cualquier colección donde el usuario escanea, elige una y entra al detalle.",
          "",
          "Trae todo resuelto: avatar/inicial circular, título + subtítulo, métricas en línea, badge de estado, menú kebab `⋮` de acciones (con `stopPropagation` para no disparar el `onClick` de la tarjeta), y estados `selected` / `inactive`. Sus compañeros `EntityInfoCardSkeleton` y `EntityInfoCardEmpty` cubren carga y vacío sin que armes nada a mano.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** la uses para una tabla densa de muchas columnas comparables → usa una tabla/`DataTable`.",
          "- **No** rearmes la grilla a mano: el contenedor lista/detalle es `EntityWorkspaceLayout`, que ya orquesta la grilla de estas tarjetas.",
          "- **No** metas formularios dentro de la tarjeta: es de lectura + navegación, no de edición.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof EntityInfoCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    title: "Dra. Valentina Suárez",
    subtitle: "Cardiología",
    initials: "VS",
    accentClass: "border-t-agent-lisa",
    metrics: [
      { label: "Pacientes", value: "248" },
      { label: "Agenda hoy", value: "12" },
    ],
    status: { label: "Activa", variant: "default" },
    actions: [
      { id: "open", label: "Abrir ficha", onSelect: () => {} },
      { id: "edit", label: "Editar", onSelect: () => {} },
      {
        id: "deactivate",
        label: "Desactivar",
        onSelect: () => {},
        separatorBefore: true,
        destructive: true,
      },
    ],
    ariaLabel: "Dra. Valentina Suárez, Cardiología",
  },
};

export const WithIcon: Story = {
  args: {
    title: "Consultorio Odontológico Sonríe",
    subtitle: "Sucursal Palermo · Buenos Aires",
    icon: <Stethoscope className="h-6 w-6" />,
    accentClass: "border-t-agent-adrian",
    metrics: [
      { label: "Profesionales", value: "6" },
      { label: "Turnos/sem.", value: "184" },
    ],
    status: { label: "Activa", variant: "default" },
  },
};

export const Selected: Story = {
  args: {
    ...Default.args,
    selected: true,
  },
};

export const Inactive: Story = {
  args: {
    title: "Dr. Tomás Figueroa",
    subtitle: "Dermatología",
    initials: "TF",
    inactive: true,
    status: { label: "Inactiva", variant: "secondary" },
  },
};

export const Loading: Story = {
  args: { title: "" },
  render: () => <EntityInfoCardSkeleton />,
  parameters: { docs: { description: { story: "Skeleton de carga (`EntityInfoCardSkeleton`)." } } },
};

export const Empty: Story = {
  args: { title: "" },
  render: () => (
    <EntityInfoCardEmpty
      title="Sin profesionales aún"
      description="Cuando cargues profesionales en esta clínica, aparecerán aquí."
    />
  ),
  parameters: {
    docs: { description: { story: "Estado vacío (`EntityInfoCardEmpty`)." } },
  },
};

/** C2-T4 · consumer story — slot `footer` ejercido con badge de urgencia custom.
 *  Demuestra composición: la marca agrega contenido custom sin tocar el card interno. */
export const ConSlotFooter: Story = {
  name: "Con slot footer (C2-T4)",
  args: {
    title: "Dra. Carolina Méndez",
    subtitle: "Traumatología",
    initials: "CM",
    accentClass: "border-t-agent-mateo",
    metrics: [
      { label: "Consultas hoy", value: "9" },
      { label: "Lista de espera", value: "14" },
    ],
    status: { label: "Activa", variant: "default" },
    footer: (
      <span className="inline-flex items-center gap-1 rounded-md bg-warning/15 px-2 py-0.5 text-xs font-medium text-warning-foreground">
        ⚠ Lista de espera crítica
      </span>
    ),
  },
  parameters: {
    docs: {
      description: {
        story:
          "Slot `footer` (C2-T4): contenido custom inyectado debajo del chip de estado sin tocar el componente interno. La marca puede añadir badges, CTAs o métricas adicionales. Sin `footer` → no renderiza nada extra (back-compat total).",
      },
    },
  },
};
