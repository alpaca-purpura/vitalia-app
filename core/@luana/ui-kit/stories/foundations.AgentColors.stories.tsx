import type { Meta, StoryObj } from "@storybook/nextjs";

import { type ShellAgentDescriptor } from "../src";
import { getBrandFixtures, type BrandFixtureSet } from "./_shell-fixtures";

/**
 * Foundations doc — NOT a component. Renders the agent palette of the brand picked
 * by the toolbar `Marca` global (vitalia OR nicolify) so the catalog explains the
 * color-per-agent system (the spine of the shell/chat) and how a brand wires it.
 * Mirror of each brand's _agent-tw-classes.ts contract.
 */
const meta = {
  title: "Foundations/Colores de agente",
  tags: ["autodocs"],
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        component: [
          "## Qué es",
          "",
          "Cada **trabajador** (agente/módulo) tiene un **color de marca**. Es identidad, no decoración: tiñe su pestaña en el Ribbon, su panel de chat, su burbuja activa y sus acentos. Una persona reconoce *con quién está hablando* por el color antes de leer el nombre.",
          "",
          "El kit es **brand-agnostic** (RN-2): no conoce los colores. La marca inyecta dos cosas en el mount del shell:",
          "",
          "1. el **catálogo de agentes** (`name`, `role`, `colorToken`…),",
          "2. una función **`getAgentClasses(slug)`** que devuelve un *bundle* de 4 clases Tailwind.",
          "",
          "Los componentes del shell consumen ese bundle — nunca hardcodean un color.",
          "",
          "## El bundle de 4 clases — cuándo usar cada una",
          "",
          "| Clase | Token | Cuándo usarla |",
          "|---|---|---|",
          "| `accentBg` | `bg-agent-{slug}` | Relleno **sólido**: pestaña activa del Ribbon, burbuja del usuario, badge de estado activo, botón primario del agente. |",
          "| `softBg` | `bg-agent-{slug}-soft` | Fondo **suave** (tinte): chip del agente, fila resaltada, fondo de `TypingIndicator`, card seleccionada. |",
          "| `accentText` | `text-agent-{slug}` | **Texto/ícono** con el color del agente sobre fondo claro o soft: nombre del agente, sub-tab activa, ícono. |",
          "| `accentBorder` | `border-agent-{slug}` | **Borde** de acento: card activa, indicador de pestaña, anillo de avatar. |",
          "",
          "## ⚠️ Excepción de contraste",
          "",
          "Cuando el color de un agente es muy claro u oscuro, **falla WCAG AA** como `text-agent-*` sobre su propio fondo soft. En **Vitalia** esto pasa con el amarillo de **Mateo** (`#FEE209`) y el casi-negro de **Lucas** (`#111111`): su `accentText` cae a **`text-foreground`** (excepciones D18/D20). El `accentBg`/`softBg`/`accentBorder` se usan igual. En **Nicolify** el roster del Ribbon no necesita excepción (todos los colores pasan AA como texto). Toda marca aplica la misma regla a sus agentes de color extremo.",
          "",
          "## ★ Contrato del JIT — clases LITERALES, nunca template",
          "",
          "`getAgentClasses` **debe** devolver strings literales con un `switch` (`case \"lisa\": return { accentBg: \"bg-agent-lisa\", … }`). **NUNCA** `` `bg-agent-${slug}` ``: el JIT de Tailwind v4 solo emite las clases que ve verbatim en el source; un string construido se purga a nada → render gris/negro. Es el mismo trap que el bug del chart negro. Por eso vitalia usa un `switch` literal en `_agent-tw-classes.ts`.",
          "",
          "## Supervisor ≠ los del Ribbon",
          "",
          "El **supervisor** vive en el sidebar (no es una pestaña del Ribbon): **Valeria** (púrpura) en Vitalia, **Luana** (indigo) en Nicolify. Los **5 del Ribbon** son la cadena de valor — Vitalia: Lisa · Lucas · Adrián · Mateo · Camila · Nicolify: Abel · Brenda · Christian · Sara · Norvil. La paleta de abajo muestra los 6 (supervisor primero).",
          "",
          "## 🎨 Cambiar de marca (toolbar)",
          "",
          "El selector **Marca** de la toolbar (arriba) intercambia TODO por marca: los **tokens de superficie + forma** (ej. el `Button` rinde **8px + cian** en Vitalia y **pill + indigo** en Nicolify) **y la paleta de agente** — los nombres, roles, colores y avatares de abajo cambian según la marca. Mismo componente, datos de cada marca; el kit no conoce ningún nombre de marca (la marca inyecta su catálogo + `getAgentClasses`).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

/** One swatch row: solid · soft+text · border, labelled with the token name. */
function AgentSwatch({
  agent,
  fixtures,
}: {
  agent: ShellAgentDescriptor;
  fixtures: BrandFixtureSet;
}) {
  const c = fixtures.getAgentClasses(agent.slug);
  const isSupervisor = agent.slug === fixtures.supervisor.slug;
  // The contrast exception is whatever brand maps accentText off the agent color.
  const contrastException = c.accentText === "text-foreground";
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="mb-3 flex items-center gap-3">
        <span
          className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold text-white ${c.accentBg}`}
        >
          {agent.initial}
        </span>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-foreground">{agent.name}</span>
            <span className="rounded-pill bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              {isSupervisor ? "supervisora · sidebar" : "ribbon"}
            </span>
          </div>
          <p className="truncate text-xs text-muted-foreground">{agent.role}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 text-xs">
        <div>
          <div className={`mb-1 h-10 rounded-md ${c.accentBg}`} />
          <code className="text-[11px] text-muted-foreground">{c.accentBg}</code>
        </div>
        <div>
          <div
            className={`mb-1 flex h-10 items-center justify-center rounded-md font-medium ${c.softBg} ${c.accentText}`}
          >
            Aa
          </div>
          <code className="text-[11px] text-muted-foreground">
            {c.softBg} · {c.accentText}
          </code>
        </div>
        <div>
          <div className={`mb-1 h-10 rounded-md border-2 bg-background ${c.accentBorder}`} />
          <code className="text-[11px] text-muted-foreground">{c.accentBorder}</code>
        </div>
      </div>

      {contrastException && (
        <p className="mt-2 text-[11px] text-muted-foreground">
          ⚠️ contraste: <code>accentText</code> → <code>text-foreground</code> (color extremo falla AA).
        </p>
      )}
    </div>
  );
}

export const Paleta: Story = {
  name: "Paleta (los 6 agentes)",
  render: (_args, { globals }) => {
    const fixtures = getBrandFixtures(globals.brand as string | undefined);
    return (
      <div className="grid grid-cols-1 gap-3 p-6 sm:grid-cols-2 lg:grid-cols-3">
        {fixtures.agentsAll.map((agent) => (
          <AgentSwatch key={agent.slug} agent={agent} fixtures={fixtures} />
        ))}
      </div>
    );
  },
};
