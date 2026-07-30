// cap: platform.design-tokens-theme
// story-origin: TBD
"use client";

/**
 * /test-stack/primitives — Visual baseline page F1-S0 (vitalia-fase1-stack-stability)
 *
 * Renderiza los 8 primitivos Shadcn instalados en F1-S0 con todas sus
 * variantes. Usa datos LatAm realistas (clínica médica Argentina).
 *
 * Origen 2026-05-22: builder-frontend dejó este componente como fixture
 * en e2e/__test-pages__/ pero el spec dev-stack-baseline.spec.ts navega a
 * /test-stack/primitives — sin esta página Next.js wrapper, Playwright 404.
 * Lifted to src/app/test-stack/ para servirlo via Next.js dev server.
 *
 * Esta página NO está protegida por Clerk auth (sin (auth) route group) — es
 * una preview pública dev-only. NO incluye datos sensibles PHI reales (solo
 * placeholders LatAm de ejemplo).
 */
import * as React from "react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { AGENT_LIST } from "@/lib/agents";

export default function PrimitivesShowcasePage(): React.ReactElement {
  return (
    <TooltipProvider>
      <main className="bg-background text-foreground min-h-screen p-8 space-y-10">
        <h1 className="text-2xl font-semibold text-foreground">
          Vitalia — Primitivos Shadcn (F1-S0 Baseline)
        </h1>

        {/* ── Buttons ─────────────────────────────────────────────────── */}
        <section aria-label="Variantes de botón" className="space-y-3">
          <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Button
          </h2>
          <div className="flex flex-wrap gap-3">
            <Button variant="default">Reservar turno</Button>
            <Button variant="secondary">Ver historial</Button>
            <Button variant="ghost">Cancelar</Button>
            <Button variant="destructive">Eliminar paciente</Button>
            <Button variant="outline">Exportar PDF</Button>
            <Button variant="link">Ver más información</Button>
            <Button disabled>Procesando...</Button>
            <Button size="sm">Pequeño</Button>
            <Button size="lg">Confirmar pago</Button>
            <Button size="icon" aria-label="Cerrar">
              ×
            </Button>
          </div>
        </section>

        {/* ── Avatar ──────────────────────────────────────────────────── */}
        {/* Agentes Vitalia con thumbnail real + ring del color agent-{slug}.
            Doctores genéricos con fallback iniciales — sin imagen src real.
            Ring offset blanco para destacar contorno sobre fondo claro. */}
        <section
          aria-label="Avatares — agentes Vitalia + doctores"
          className="space-y-3"
        >
          <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Avatar
          </h2>
          <div className="flex gap-4 items-end">
            {/* Agentes con foto real + ring color del agente.
                Inline style usado porque Tailwind v4 NO genera utilities dinámicas
                tipo ring-agent-${slug} (no detecta clases con interpolación).
                Hex color de SSoT @/lib/agents → CSS var --tw-ring-color override. */}
            {AGENT_LIST.map((agent) => (
              <div
                key={agent.slug}
                className="flex flex-col items-center gap-1.5"
              >
                <Avatar
                  className="size-12 ring-4 ring-offset-2 ring-offset-background"
                  style={
                    { "--tw-ring-color": agent.colorHex } as React.CSSProperties
                  }
                  aria-label={`${agent.name} — ${agent.role}`}
                >
                  <AvatarImage src={agent.thumbnail} alt={agent.name} />
                  <AvatarFallback
                    className="text-white font-bold"
                    style={{ backgroundColor: agent.colorHex }}
                  >
                    {agent.name.slice(0, 1)}
                  </AvatarFallback>
                </Avatar>
                <span className="text-xs text-muted-foreground font-medium">
                  {agent.name}
                </span>
              </div>
            ))}
            {/* Doctores genéricos — fallback iniciales (sin foto real) */}
            <div className="flex flex-col items-center gap-1.5">
              <Avatar className="size-12 ring-2 ring-offset-2 ring-offset-background ring-border">
                <AvatarFallback className="bg-muted text-muted-foreground font-bold">
                  VS
                </AvatarFallback>
              </Avatar>
              <span className="text-xs text-muted-foreground font-medium">
                Dra. Soria
              </span>
            </div>
            <div className="flex flex-col items-center gap-1.5">
              <Avatar className="size-12 ring-2 ring-offset-2 ring-offset-background ring-border">
                <AvatarFallback className="bg-muted text-muted-foreground font-bold">
                  MR
                </AvatarFallback>
              </Avatar>
              <span className="text-xs text-muted-foreground font-medium">
                Dr. Ruiz
              </span>
            </div>
          </div>
        </section>

        {/* ── Input ───────────────────────────────────────────────────── */}
        <section
          aria-label="Campos de formulario"
          className="space-y-3 max-w-sm"
        >
          <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Input
          </h2>
          <Input placeholder="Nombre del paciente" defaultValue="" />
          <Input placeholder="DNI: 25.xxx.xxx" type="text" />
          <Input placeholder="Teléfono: +54 11 xxxx-xxxx" type="tel" />
          <Input placeholder="Email institucional" type="email" disabled />
        </section>

        {/* ── Badge ───────────────────────────────────────────────────── */}
        <section aria-label="Badges de estado" className="space-y-3">
          <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Badge
          </h2>
          <div className="flex flex-wrap gap-2">
            <Badge variant="default">Activo</Badge>
            <Badge variant="secondary">Pendiente</Badge>
            <Badge variant="destructive">Cancelado</Badge>
            <Badge variant="outline">Nueva consulta</Badge>
            <Badge variant="default" className="bg-agent-lisa text-white">
              Obra social OSDE
            </Badge>
            <Badge variant="default" className="bg-agent-valeria text-white">
              Prepago Swiss Medical
            </Badge>
            <Badge variant="default" className="bg-agent-camila text-white">
              Particular
            </Badge>
          </div>
        </section>

        {/* ── Textarea ────────────────────────────────────────────────── */}
        <section
          aria-label="Área de texto médico"
          className="space-y-3 max-w-sm"
        >
          <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Textarea
          </h2>
          <Textarea placeholder="Notas clínicas de la consulta..." rows={3} />
          <Textarea
            defaultValue="Paciente con antecedentes de HTA. Se indica control en 30 días."
            rows={3}
            readOnly
          />
        </section>

        {/* ── Tabs ────────────────────────────────────────────────────── */}
        <section
          aria-label="Pestañas de historial"
          className="space-y-3 max-w-md"
        >
          <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Tabs
          </h2>
          <Tabs defaultValue="consultas">
            <TabsList>
              <TabsTrigger value="consultas">Consultas</TabsTrigger>
              <TabsTrigger value="estudios">Estudios</TabsTrigger>
              <TabsTrigger value="recetas">Recetas</TabsTrigger>
            </TabsList>
            <TabsContent
              value="consultas"
              className="p-3 text-sm text-muted-foreground"
            >
              23/04/2026 — Control cardíaco con Dr. Ruiz
            </TabsContent>
            <TabsContent
              value="estudios"
              className="p-3 text-sm text-muted-foreground"
            >
              ECG 12/03/2026 — Ritmo sinusal normal
            </TabsContent>
            <TabsContent
              value="recetas"
              className="p-3 text-sm text-muted-foreground"
            >
              Enalapril 10mg — 30 comprimidos (renovación mensual)
            </TabsContent>
          </Tabs>
        </section>

        {/* ── Tooltip ─────────────────────────────────────────────────── */}
        <section aria-label="Tooltips informativos" className="space-y-3">
          <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Tooltip
          </h2>
          <div className="flex gap-4">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm">
                  OSDE
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                Obra Social de Empleados de Comercio
              </TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm">
                  IOMA
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                Instituto de Obra Médico Asistencial
              </TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Información">
                  ℹ
                </Button>
              </TooltipTrigger>
              <TooltipContent>Turno confirmado vía WhatsApp</TooltipContent>
            </Tooltip>
          </div>
        </section>

        {/* ── DropdownMenu ────────────────────────────────────────────── */}
        <section aria-label="Menú de acciones" className="space-y-3">
          <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            DropdownMenu
          </h2>
          <div className="flex gap-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">Acciones del paciente</Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuLabel>Gestión</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>Ver ficha completa</DropdownMenuItem>
                <DropdownMenuItem>Agendar turno</DropdownMenuItem>
                <DropdownMenuItem>Enviar recordatorio</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem variant="destructive">
                  Dar de baja
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </section>
      </main>
    </TooltipProvider>
  );
}
