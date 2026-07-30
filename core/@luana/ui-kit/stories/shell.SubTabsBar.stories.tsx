import type { Meta, StoryObj } from "@storybook/nextjs";

import { SubTabsBar, type ShellSubTabMeta } from "../src";
import {
  ALL_AGENTS_BY_SLUG,
  ALL_SUBTABS_BY_AGENT,
  getAnyBrandAgentClasses,
} from "./_shell-fixtures";

/**
 * ★ react-docgen-typescript (autodocs) stamps `displayName` + `__docgenInfo` as
 * ENUMERABLE props onto every exported object — so Object.entries(...) yields phantom
 * `["displayName", <string>]` / `["__docgenInfo", <obj>]` entries. SubTabsBar does
 * `Object.entries(subTabsByAgent).map(([k, tabs]) => tabs.map(...))` → `tabs.map is not
 * a function` on the string. Rebuild a clean Record keyed only by real slugs.
 *
 * ★ Brand switch: SubTabsBar derives its active agent from usePathname() (a STATIC
 *   navigation mock that can't read the `brand` global), so the active SUB-TAB set
 *   stays pinned per story. The union catalog/subtabs covers both brands' slugs and
 *   getAnyBrandAgentClasses returns a valid bundle; the agent COLOR still follows the
 *   brand because the bg-agent-* token VALUE is brand-keyed in preview.css [data-brand].
 *   (To see nicolify sub-tabs, use the nicolify-pinned stories below.)
 */
const SUBTABS_BY_AGENT: Record<string, ShellSubTabMeta[]> = { ...ALL_SUBTABS_BY_AGENT };

/**
 * Story consumes the REAL SubTabsBar from src/. It reads usePathname/useParams
 * (next/navigation) → @storybook/nextjs mocks them via parameters.nextjs.navigation.
 *
 * ★ Props are passed LITERALLY via `render` (not Storybook args): the Controls
 *   addon deep-clones object args and turns the Record's nested arrays into
 *   index-objects → `tabs.map is not a function`. A literal render bypasses that.
 */
const meta = {
  title: "Shell/SubTabsBar",
  component: SubTabsBar,
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
          "El `SubTabsBar` es la **navegación N2**: las sub-secciones del agente activo (Resumen / Agenda / Tareas…). Franja full-bleed con el mismo lenguaje que el Ribbon; el activo toma el color soft del agente. Se deriva de la URL y **se oculta solo** (devuelve `null`) cuando el agente no tiene sub-tabs.",
          "",
          "Va debajo del `Ribbon`. La marca inyecta `subTabsByAgent`.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **3+ vistas discretas dentro de una sub-tab** → `SubSubTabsBar` (N3-static), nunca Tabs internas en el body.",
          "- **Tabs de contenido dentro de una hoja** → `Tabs` / `TogglePill`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof SubTabsBar>;

export default meta;
type Story = StoryObj<typeof meta>;

const Demo = () => (
  <SubTabsBar
    agentCatalog={ALL_AGENTS_BY_SLUG}
    subTabsByAgent={SUBTABS_BY_AGENT}
    getAgentClasses={getAnyBrandAgentClasses}
    onNavigate={() => {}}
  />
);

export const Mateo: Story = {
  name: "Mateo (Agenda activa)",
  render: () => <Demo />,
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
  name: "Lisa (Marca activa · 4 sub-tabs)",
  render: () => <Demo />,
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/lisa/marca",
        segments: [["tenantId", "clinica"], "lisa", "marca"],
      },
    },
  },
};

export const Adrian: Story = {
  name: "Adrián (Inbox activa · 5 sub-tabs)",
  render: () => <Demo />,
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/adrian/inbox",
        segments: [["tenantId", "clinica"], "adrian", "inbox"],
      },
    },
  },
};

export const Lucas: Story = {
  name: "Lucas (Lanzar activa · 5 sub-tabs)",
  render: () => <Demo />,
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/lucas/lanzar",
        segments: [["tenantId", "clinica"], "lucas", "lanzar"],
      },
    },
  },
};

export const Camila: Story = {
  name: "Camila (Voz del paciente activa · 4 sub-tabs)",
  render: () => <Demo />,
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/camila/voz",
        segments: [["tenantId", "clinica"], "camila", "voz"],
      },
    },
  },
};

/* ── Nicolify-pinned (switch the Marca global to nicolify to see brand colors) ── */

export const ChristianNicolify: Story = {
  name: "Christian · Pipeline (nicolify · 6 sub-tabs)",
  render: () => <Demo />,
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/agencia/christian/pipeline",
        segments: [["tenantId", "agencia"], "christian", "pipeline"],
      },
    },
  },
};

export const AbelNicolify: Story = {
  name: "Abel · ICP (nicolify · 3 sub-tabs)",
  render: () => <Demo />,
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/agencia/abel/icp",
        segments: [["tenantId", "agencia"], "abel", "icp"],
      },
    },
  },
};
