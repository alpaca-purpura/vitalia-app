"use client";

/**
 * PrimitivesShowcase — Fixture Playwright para visual baseline F1-S0
 *
 * Renderiza los 8 primitivos Shadcn instalados en F1-S0 con todas sus
 * variantes. Usa datos LatAm realistas (clínica médica Argentina).
 *
 * NO es una ruta Next.js de producción. Es un fixture de test visual.
 * Path: e2e/__test-pages__/stack-stability/primitives-showcase.tsx
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

export function PrimitivesShowcase(): React.ReactElement {
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
        <section aria-label="Avatar médico" className="space-y-3">
          <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Avatar
          </h2>
          <div className="flex gap-4 items-center">
            <Avatar className="size-10">
              <AvatarImage src="" alt="Dra. Valentina Soria" />
              <AvatarFallback>VS</AvatarFallback>
            </Avatar>
            <Avatar className="size-10">
              <AvatarImage src="" alt="Dr. Marcos Ruiz" />
              <AvatarFallback>MR</AvatarFallback>
            </Avatar>
            <Avatar className="size-10 bg-agent-lisa">
              <AvatarFallback className="bg-agent-lisa text-white font-bold">
                L
              </AvatarFallback>
            </Avatar>
            <Avatar className="size-10 bg-agent-valeria">
              <AvatarFallback className="bg-agent-valeria text-white font-bold">
                V
              </AvatarFallback>
            </Avatar>
            <Avatar className="size-10 bg-agent-camila">
              <AvatarFallback className="bg-agent-camila text-white font-bold">
                C
              </AvatarFallback>
            </Avatar>
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
