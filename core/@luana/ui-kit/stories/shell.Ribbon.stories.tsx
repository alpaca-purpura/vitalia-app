import type { Meta, StoryObj } from "@storybook/nextjs";

import { Ribbon } from "../src";
import { getBrandFixtures } from "./_shell-fixtures";

/**
 * Story consumes the REAL Ribbon from src/. The catalog + order + getAgentClasses +
 * config label all come from the brand picked by the toolbar `Marca` global, so a
 * brand switch flips the agent NAMES, COLORS and avatars — not just the surface CSS.
 * The active tab is URL-derived from the injected `pathname`; each story names the
 * active agent by its index in the (brand-specific) ribbon order, so it stays
 * coherent under either brand.
 */
const meta = {
  title: "Shell/Ribbon",
  component: Ribbon,
  decorators: [
    (Story) => (
      <div className="w-[760px] max-w-full overflow-hidden rounded-lg border border-border">
        <Story />
      </div>
    ),
  ],
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "El `Ribbon` es la **navegación N1 del shell**: la fila de agentes (tab por trabajador) + la pestaña Plataforma al final. Es el sesgo de ruteo del producto — el usuario elige con quién trabaja (PARADIGM: trabajadores sobre un sistema). Cada tab toma el color del agente; el activo se deriva de la URL (no hay estado de selección a mano). Tablist accesible (flechas/Home/End/Enter).",
          "",
          "Se monta una sola vez, arriba del shell, debajo del `TopBarShell`. La marca inyecta su catálogo + orden + `getAgentClasses`. El selector **Marca** de la toolbar cambia el roster: Vitalia (Lisa/Lucas/Adrián/Mateo/Camila) ↔ Nicolify (Abel/Brenda/Christian/Sara/Norvil).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Sub-secciones de un agente** → `SubTabsBar` (N2), no más tabs en el ribbon.",
          "- **Navegación de una hoja lista/detalle** → `EntitySubNavBar` (N3), dentro del panel.",
          "- **No** lo uses para acciones (botones) — es navegación entre agentes.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Ribbon>;

export default meta;
type Story = StoryObj<typeof meta>;

/** Render the Ribbon with the active agent = the ribbon agent at `activeIndex`. */
function renderRibbon(activeIndex: number | "config"): Story["render"] {
  return function RibbonRender(_args, { globals }) {
    const f = getBrandFixtures(globals.brand as string | undefined);
    const pathname =
      activeIndex === "config"
        ? "/app/config"
        : `/app/${f.ribbonOrder[activeIndex]}/${f.agentsBySlug[f.ribbonOrder[activeIndex]].defaultSubtab || "x"}`;
    return (
      <Ribbon
        agentCatalog={f.agentsRibbon}
        ribbonOrder={f.ribbonOrder}
        getAgentClasses={f.getAgentClasses}
        configTabSlug="config"
        configTabLabel={f.configTabLabel}
        onNavigate={() => {}}
        pathname={pathname}
      />
    );
  };
}

export const PrimerAgente: Story = {
  name: "Primer agente activo",
  render: renderRibbon(0),
};

export const SegundoAgente: Story = {
  name: "Segundo agente activo",
  render: renderRibbon(1),
};

export const TercerAgente: Story = {
  name: "Tercer agente activo",
  render: renderRibbon(2),
};

export const CuartoAgente: Story = {
  name: "Cuarto agente activo",
  render: renderRibbon(3),
};

export const QuintoAgente: Story = {
  name: "Quinto agente activo",
  render: renderRibbon(4),
};

export const PlataformaActiva: Story = {
  name: "Plataforma activa",
  render: renderRibbon("config"),
};
