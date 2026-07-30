import type { Meta, StoryObj } from "@storybook/nextjs";
import type { ReactNode } from "react";

import { TopBarShell } from "../src";
import { getBrandFixtures, type BrandFixtureSet, useDemoShellStore } from "./_shell-fixtures";

/** Demo right cluster (a real brand injects ThemeToggle + TenantSwitcher). */
function rightCluster(f: BrandFixtureSet): ReactNode {
  const tenantName = f.brand === "nicolify" ? "Agencia Demo" : "Sonrisa Plena";
  const tenantInitials = f.brand === "nicolify" ? "AD" : "SP";
  return (
    <>
      <button
        type="button"
        className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-muted"
        aria-label="Cambiar tema"
      >
        <span aria-hidden="true">🌙</span>
      </button>
      <button
        type="button"
        className="flex h-8 items-center gap-2 rounded-md border border-border px-2.5 text-sm hover:bg-muted"
      >
        <span
          className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-semibold ${f.getAgentClasses(f.supervisor.slug).softBg}`}
        >
          {tenantInitials}
        </span>
        <span className="text-foreground">{tenantName}</span>
      </button>
    </>
  );
}

/**
 * Story consumes the REAL TopBarShell from src/. The interactive variant
 * subscribes the injected shell store (mobile burger); the skeleton variant is
 * store-free (renders outside the ssr:false boundary). Logo + supervisor name +
 * tenant chip follow the toolbar `Marca` global (vitalia ↔ nicolify).
 */
const meta = {
  title: "Shell/TopBarShell",
  component: TopBarShell,
  decorators: [
    (Story) => (
      <div className="w-[860px] max-w-full overflow-hidden rounded-lg border border-border">
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
          "El `TopBarShell` es la **barra global** del shell: logo de marca a la izquierda + cluster de marca a la derecha (tema, selector de tenant) + hamburguesa en mobile. Es transversal — usa `--primary` (no color de agente). La marca inyecta los slots (`logoSlot`, `rightClusterSlot`).",
          "",
          "Variantes: `interactive` (suscribe el store del shell para el drawer mobile) y `skeleton` (store-free, para renderizar fuera del límite `ssr:false` sin tocar la persistencia).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Cabecera de una hoja** → `PageHeader`.",
          "- **Navegación entre agentes** → `Ribbon`, no la barra global.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof TopBarShell>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Interactivo: Story = {
  name: "Interactivo",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <TopBarShell
        variant="interactive"
        useShellStore={useDemoShellStore}
        supervisorName={f.supervisor.name}
        logoSlot={<f.Logo />}
        rightClusterSlot={rightCluster(f)}
      />
    );
  },
};

export const Skeleton: Story = {
  name: "Skeleton (SSR, store-free)",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <TopBarShell
        variant="skeleton"
        supervisorName={f.supervisor.name}
        logoSlot={<f.Logo />}
        rightClusterSlot={rightCluster(f)}
      />
    );
  },
};

export const Movil: Story = {
  name: "Móvil (hamburguesa)",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <TopBarShell
        variant="interactive"
        useShellStore={useDemoShellStore}
        supervisorName={f.supervisor.name}
        logoSlot={<f.Logo />}
        rightClusterSlot={rightCluster(f)}
      />
    );
  },
  globals: { viewport: { value: "mobile" } },
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        story:
          "En <1024 el TopBar muestra la hamburguesa (abre el drawer del supervisor). El logo y el cluster de marca se compactan.",
      },
    },
  },
};
