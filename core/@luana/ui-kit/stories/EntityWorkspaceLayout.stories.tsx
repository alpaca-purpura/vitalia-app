import type { Meta, StoryObj } from "@storybook/nextjs";

import { EntityWorkspaceLayout } from "../src/EntityWorkspaceLayout";
import { type EntitySubNavLeaf } from "../src/EntitySubNavBar";

/**
 * Story consumes the REAL EntityWorkspaceLayout from src/. It uses next/navigation
 * (useParams) → @storybook/nextjs mocks it (preview: nextjs.appDirectory).
 */
const leaves: EntitySubNavLeaf[] = [
  { id: "ficha", label: "Ficha", href: "/clinica/palermo/ficha", isPrimary: true },
  { id: "agenda", label: "Agenda", href: "/clinica/palermo/agenda" },
  { id: "equipo", label: "Equipo", href: "/clinica/palermo/equipo" },
  { id: "servicios", label: "Servicios", href: "/clinica/palermo/servicios" },
];

const PanelContent = () => (
  <div className="p-6">
    <h2 className="mb-2 text-lg font-semibold text-foreground">Agenda · Sucursal Palermo</h2>
    <p className="text-sm text-muted-foreground">
      Aquí el detalle de la hoja activa. El layout solo orquesta la navegación N3; el
      contenido lo aporta la feature como <code>children</code>.
    </p>
  </div>
);

const meta = {
  title: "Organisms/EntityWorkspaceLayout",
  component: EntityWorkspaceLayout,
  tags: ["autodocs"],
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es el **contenedor canónico de toda vista lista/detalle de 1 panel** (canon §2.1-2.2). Orquesta el patrón completo: en modo *master* muestra la grilla de `EntityInfoCard`; en modo *detalle* muestra la franja `EntitySubNavBar` full-bleed + la hoja activa. Lo dirige la URL — no hay estado de selección a mano.",
          "",
          "Úsalo SIEMPRE que una superficie sea \"colección de entidades → entrar a una → ver/editar sus secciones\": clínicas, doctores, pacientes, servicios, campañas, leads. Trae el skeleton de carga store-free (SSR-safe) vía `isLoading`, así no parpadea.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** cablees el list/detail a mano (grilla + sub-nav por separado en cada feature) — esa duplicación es justo lo que este componente elimina (canon §2.2).",
          "- **No** lo uses para un dashboard sin entidad seleccionable, ni para un wizard de pasos.",
          "- **No** lo uses si necesitás dos paneles persistentes lado a lado (master+detalle simultáneos) — este patrón es URL-driven de 1 panel.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof EntityWorkspaceLayout>;

export default meta;
type Story = StoryObj<typeof meta>;

export const DetailMode: Story = {
  args: {
    rootHref: "/clinicas",
    rootLabel: "Clínicas",
    entity: { id: "palermo", name: "Sucursal Palermo" },
    leaves,
    activeLeaf: "agenda",
    onAddAffordance: () => {},
    children: <PanelContent />,
  },
};

export const MasterMode: Story = {
  args: {
    rootHref: "/clinicas",
    rootLabel: "Clínicas",
    entity: null,
    leaves,
    activeLeaf: null,
    placeholder: "Elige una clínica de la lista para ver su workspace",
    children: (
      <div className="p-6 text-sm text-muted-foreground">
        Grilla de clínicas (modo master). En producción son tarjetas
        <code> EntityInfoCard</code> en grilla <code>auto-fill</code>.
      </div>
    ),
  },
};

export const Loading: Story = {
  args: {
    ...DetailMode.args,
    isLoading: true,
  },
  parameters: {
    docs: { description: { story: "Skeleton store-free mientras carga la entidad." } },
  },
};
