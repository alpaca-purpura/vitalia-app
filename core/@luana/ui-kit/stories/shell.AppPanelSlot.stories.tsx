import type { ReactNode } from "react";
import type { Meta, StoryObj } from "@storybook/nextjs";

import { AppPanelSlot, PlaceholderCard } from "../src";
import { buildCleanSubtabs, getBrandFixtures } from "./_shell-fixtures";

/**
 * Story consumes the REAL AppPanelSlot from src/ — the application-side host that
 * stacks Ribbon (N1) + SubTabsBar (N2) + SubSubTabsBar (N3) + the page content.
 *
 * AppPanelSlot reads usePathname()/useRouter() (next/navigation) internally → the
 * active agent/sub-tab/sub-sub-tab are URL-derived. @storybook/nextjs mocks them
 * via parameters.nextjs.navigation (STATIC → can't read the `brand` global), so the
 * ACTIVE highlight is pinned per story. The Ribbon roster + colors + sub-tabs DO flip
 * with the toolbar `Marca` global (the catalog/order/subtabs come via render); each
 * brand has its own pinned stories so the active highlight stays coherent.
 *
 * The wrapper gives it the panel height (h-full); AppPanelSlot fills it.
 */
const meta = {
  title: "Shell/AppPanelSlot",
  component: AppPanelSlot,
  decorators: [
    (Story) => (
      <div className="h-[560px] w-full overflow-hidden rounded-lg border border-border">
        <Story />
      </div>
    ),
  ],
  tags: ["autodocs"],
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`AppPanelSlot` es el **lado de aplicación del shell**: apila la navegación (Ribbon N1 + SubTabsBar N2 + SubSubTabsBar N3) arriba y deja la hoja debajo en un marco scrolleable. Es el panel derecho del `ShellLayout` — lo que el usuario ve al lado del supervisor. Deriva todo de la URL; las barras N2/N3 se ocultan solas cuando el agente/sub-tab no las tiene.",
          "",
          "El roster + colores del Ribbon cambian con el selector **Marca** de la toolbar (Vitalia ↔ Nicolify). Casi nunca lo montas suelto: vive dentro de `ShellLayout`.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **El shell completo** (con supervisor + split resizable) → `ShellLayout`, que monta este panel.",
          "- **Solo una barra de navegación** → `Ribbon` / `SubTabsBar` / `SubSubTabsBar` por separado.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof AppPanelSlot>;

export default meta;
type Story = StoryObj<typeof meta>;

/** Demo leaf content (so the panel shows something below the nav). */
const DemoContent = () => (
  <div className="p-6">
    <PlaceholderCard
      icon="📋"
      title="Resumen del día"
      description="Aquí vive la hoja del agente activo. El marco scrollea; las barras de navegación quedan fijas arriba."
    />
  </div>
);

/** Build a brand-aware AppPanelSlot render (catalog/order/subtabs from globals). */
function renderPanel(children?: ReactNode): Story["render"] {
  return function PanelRender(_args, { globals }) {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <AppPanelSlot
        agentCatalog={f.agentsAll}
        ribbonOrder={f.ribbonOrder}
        subTabsByAgent={buildCleanSubtabs(f)}
        subSubTabsByKey={f.subSubTabsByKey}
        getAgentClasses={f.getAgentClasses}
        configTabSlug="config"
        configTabLabel={f.configTabLabel}
        onNavigate={() => {}}
      >
        {children}
      </AppPanelSlot>
    );
  };
}

/* ── Vitalia-pinned (default Marca = vitalia) ── */

export const Mateo: Story = {
  name: "Mateo · Agenda (sin N3)",
  render: renderPanel(<DemoContent />),
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/mateo/agenda",
        segments: [["tenantId", "clinica"], "mateo", "agenda"],
      },
    },
  },
};

export const Lisa: Story = {
  name: "Lisa · Marca (con N3 Identidad/Voz y tono/Presencia)",
  render: renderPanel(<DemoContent />),
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/lisa/marca/identidad",
        segments: [["tenantId", "clinica"], "lisa", "marca", "identidad"],
      },
    },
  },
};

export const SinContenido: Story = {
  name: "Sin contenido (skeleton por defecto)",
  render: renderPanel(),
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/adrian/inbox",
        segments: [["tenantId", "clinica"], "adrian", "inbox"],
      },
    },
  },
};

/* ── Nicolify-pinned (switch the Marca global to nicolify) ── */

export const AbelNicolify: Story = {
  name: "Abel · Oferta (nicolify · con N3)",
  render: renderPanel(<DemoContent />),
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/agencia/abel/oferta/catalogo-escalera",
        segments: [["tenantId", "agencia"], "abel", "oferta", "catalogo-escalera"],
      },
    },
  },
};

export const ChristianNicolify: Story = {
  name: "Christian · Pipeline (nicolify · sin N3)",
  render: renderPanel(<DemoContent />),
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/agencia/christian/pipeline",
        segments: [["tenantId", "agencia"], "christian", "pipeline"],
      },
    },
  },
};
