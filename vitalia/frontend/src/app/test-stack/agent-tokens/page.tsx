// cap: platform.design-tokens-theme
// story-origin: TBD
"use client";

/**
 * /test-stack/agent-tokens — Visual baseline page F1-S0 (vitalia-fase1-stack-stability)
 *
 * Renderiza los 7 tokens de agente (base + soft variant) con etiqueta
 * de nombre y valor HSL. Permite verificar visualmente que los CSS vars
 * están siendo consumidos correctamente por Tailwind.
 *
 * Origen 2026-05-22: builder-frontend dejó este componente como fixture
 * en e2e/__test-pages__/ pero el spec dev-stack-baseline.spec.ts navega a
 * /test-stack/agent-tokens — sin esta página Next.js wrapper, Playwright 404.
 * Lifted to src/app/test-stack/ para servirlo via Next.js dev server.
 */
import * as React from "react";

interface SwatchProps {
  name: string;
  colorClass: string;
  softClass: string;
  hsl: string;
  softHsl: string;
  agentLabel: string;
}

function AgentSwatch({
  name,
  colorClass,
  softClass,
  hsl,
  softHsl,
  agentLabel,
}: SwatchProps): React.ReactElement {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-3">
        {/* Base color swatch */}
        <div
          className={`size-14 rounded-lg border border-border shadow-sm ${colorClass}`}
          aria-label={`Color base ${name}`}
          role="img"
        />
        {/* Soft color swatch */}
        <div
          className={`size-14 rounded-lg border border-border shadow-sm ${softClass}`}
          aria-label={`Color suave ${name}`}
          role="img"
        />
        <div className="space-y-0.5">
          <p className="text-sm font-semibold text-foreground">{agentLabel}</p>
          <p className="text-xs text-muted-foreground font-mono">{name}</p>
          <p className="text-xs text-muted-foreground font-mono opacity-70">
            base: {hsl}
          </p>
          <p className="text-xs text-muted-foreground font-mono opacity-70">
            soft: {softHsl}
          </p>
        </div>
      </div>
    </div>
  );
}

const AGENT_TOKENS: SwatchProps[] = [
  {
    name: "--agent-lisa",
    colorClass: "bg-agent-lisa",
    softClass: "bg-agent-lisa-soft",
    hsl: "156 100% 41%",
    softHsl: "156 80% 92%",
    agentLabel: "Lisa — Agenda y Reservas",
  },
  {
    name: "--agent-lucas",
    colorClass: "bg-agent-lucas",
    softClass: "bg-agent-lucas-soft",
    hsl: "0 0% 7%",
    softHsl: "0 0% 92%",
    agentLabel: "Lucas — CRM y Nutrición",
  },
  {
    name: "--agent-adrian",
    colorClass: "bg-agent-adrian",
    softClass: "bg-agent-adrian-soft",
    hsl: "198 99% 49%",
    softHsl: "197 90% 89%",
    agentLabel: "Adrián — Growth y Marketing",
  },
  {
    name: "--agent-valeria",
    colorClass: "bg-agent-valeria",
    softClass: "bg-agent-valeria-soft",
    hsl: "287 53% 37%",
    softHsl: "287 53% 90%",
    agentLabel: "Valeria — Copiloto Médico",
  },
  {
    name: "--agent-camila",
    colorClass: "bg-agent-camila",
    softClass: "bg-agent-camila-soft",
    hsl: "244 84% 32%",
    softHsl: "244 53% 92%",
    agentLabel: "Camila — Administración",
  },
  {
    name: "--agent-mateo",
    colorClass: "bg-agent-mateo",
    softClass: "bg-background",
    hsl: "53 99% 51%",
    softHsl: "N/A",
    agentLabel: "Mateo — Atención al Paciente",
  },
  {
    name: "--agent-config",
    colorClass: "bg-agent-config",
    softClass: "bg-muted",
    hsl: "240 4% 46%",
    softHsl: "N/A",
    agentLabel: "Config — Configuración",
  },
];

export default function AgentTokensSwatchPage(): React.ReactElement {
  return (
    <main className="bg-background text-foreground min-h-screen p-8 space-y-8">
      <h1 className="text-2xl font-semibold text-foreground">
        Vitalia — Agent Tokens Swatch (F1-S0 Baseline)
      </h1>
      <p className="text-sm text-muted-foreground max-w-xl">
        7 tokens de agente + variantes soft. Cada swatch consume{" "}
        <code className="font-mono text-xs bg-muted px-1 rounded">
          hsl(var(--agent-lisa))
        </code>{" "}
        (un token por agente) via Tailwind classes. Verificación empírica de que
        los CSS vars están correctamente definidos y consumidos.
      </p>

      <div
        className="grid gap-6 max-w-2xl"
        style={{ gridTemplateColumns: "1fr" }}
        aria-label="Paleta de colores de agentes"
      >
        {AGENT_TOKENS.map((token) => (
          <AgentSwatch key={token.name} {...token} />
        ))}
      </div>

      {/* Surface tokens section */}
      <section
        aria-label="Surface tokens"
        className="space-y-4 pt-8 border-t border-border"
      >
        <h2 className="text-lg font-semibold text-foreground">
          Surface Tokens (Shadcn estándar)
        </h2>
        <div className="grid grid-cols-4 gap-3 max-w-xl">
          <div className="space-y-1">
            <div className="size-12 rounded bg-background border border-border" />
            <p className="text-xs text-muted-foreground">background</p>
          </div>
          <div className="space-y-1">
            <div className="size-12 rounded bg-primary" />
            <p className="text-xs text-muted-foreground">primary</p>
          </div>
          <div className="space-y-1">
            <div className="size-12 rounded bg-accent" />
            <p className="text-xs text-muted-foreground">accent</p>
          </div>
          <div className="space-y-1">
            <div className="size-12 rounded bg-muted" />
            <p className="text-xs text-muted-foreground">muted</p>
          </div>
          <div className="space-y-1">
            <div className="size-12 rounded bg-card border border-border" />
            <p className="text-xs text-muted-foreground">card</p>
          </div>
          <div className="space-y-1">
            <div className="size-12 rounded bg-destructive" />
            <p className="text-xs text-muted-foreground">destructive</p>
          </div>
          <div className="space-y-1">
            <div className="size-12 rounded bg-secondary" />
            <p className="text-xs text-muted-foreground">secondary</p>
          </div>
          <div className="space-y-1">
            <div className="size-12 rounded border-2 border-ring" />
            <p className="text-xs text-muted-foreground">ring</p>
          </div>
        </div>
      </section>
    </main>
  );
}
