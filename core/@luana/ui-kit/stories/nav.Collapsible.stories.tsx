import type { Meta, StoryObj } from "@storybook/nextjs";
import { ChevronsUpDown } from "lucide-react";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "../src/collapsible";
import { Button } from "../src/button";

const meta = {
  title: "Molecules/Collapsible",
  component: Collapsible,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Collapsible` es para **una única sección expandible/colapsable** con trigger personalizado. Es más ligero que `Accordion` y más adecuado cuando solo hay un bloque que se quiere mostrar u ocultar, como filtros avanzados, notas adicionales opcionales, o una sección de detalles técnicos.",
          "",
          "A diferencia de `Accordion`, no gestiona múltiples ítems ni tiene estilo visual estandarizado — el consumer define completamente el trigger.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Múltiples secciones expand/collapse del mismo nivel** → usa `Accordion`.",
          "- **Secciones de navegación** → usa `Tabs`.",
          "- **Estado controlado con más lógica** → maneja el `open`/`onOpenChange` del propio `Collapsible`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Collapsible>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Collapsible className="w-80 space-y-2">
      <div className="flex items-center justify-between space-x-4 px-4">
        <h4 className="text-sm font-semibold">Notas adicionales</h4>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm">
            <ChevronsUpDown className="h-4 w-4" />
            <span className="sr-only">Expandir notas</span>
          </Button>
        </CollapsibleTrigger>
      </div>
      <CollapsibleContent className="space-y-2">
        <div className="rounded-md border px-4 py-3 text-sm">
          Paciente con antecedentes de hipertensión. Tomar presión antes de la consulta.
        </div>
        <div className="rounded-md border px-4 py-3 text-sm">
          Prefiere turnos en la mañana. Contactar solo por WhatsApp.
        </div>
      </CollapsibleContent>
    </Collapsible>
  ),
};

export const Abierto: Story = {
  name: "Abierto por defecto",
  render: () => (
    <Collapsible open className="w-80 space-y-2">
      <div className="flex items-center justify-between space-x-4 px-4">
        <h4 className="text-sm font-semibold">Filtros avanzados</h4>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm">
            <ChevronsUpDown className="h-4 w-4" />
          </Button>
        </CollapsibleTrigger>
      </div>
      <CollapsibleContent className="space-y-2">
        <div className="rounded-md border px-4 py-3 text-sm text-muted-foreground">
          Especialidad · Cobertura · Modalidad · Día de semana
        </div>
      </CollapsibleContent>
    </Collapsible>
  ),
};
