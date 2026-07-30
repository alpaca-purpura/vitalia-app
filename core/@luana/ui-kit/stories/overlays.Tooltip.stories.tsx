import type { Meta, StoryObj } from "@storybook/nextjs";
import { Info, HelpCircle } from "lucide-react";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../src/tooltip";
import { Button } from "../src/button";

const meta = {
  title: "Molecules/Tooltip",
  component: Tooltip,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Tooltip` muestra una etiqueta de texto breve al hacer **hover** sobre un elemento. Ideal para describir íconos sin etiqueta visible, explicar campos de configuración avanzada, o dar contexto a una métrica.",
          "",
          "Siempre envuelve el árbol en `TooltipProvider` (normalmente en el layout raíz de la app). El contenido debe ser texto corto (máximo 2 líneas).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Contenido interactivo (formularios, botones)** → usa `Popover` (el tooltip no puede recibir foco).",
          "- **Información extensa o multilinea** → usa `Popover` con `PopoverContent`.",
          "- **Mensajes de error** → usa el mensaje de validación del formulario, no un tooltip.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Tooltip>;

export default meta;
type Story = StoryObj<typeof meta>;

// Story con tooltip visible para revisión directa
export const Visible: Story = {
  name: "Visible (revisión directa)",
  render: () => (
    <TooltipProvider>
      <div className="flex items-center justify-center py-8">
        <Tooltip open>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="Información">
              <Info className="h-5 w-5 text-muted-foreground" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Matrícula profesional verificada por el sistema</p>
          </TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  ),
  parameters: {
    layout: "padded",
    docs: {
      description: {
        story:
          "Tooltip forzado `open` para revisión directa. En producción aparece al hacer hover.",
      },
    },
  },
};

export const EnIcono: Story = {
  name: "En ícono de ayuda",
  render: () => (
    <TooltipProvider>
      <div className="flex items-center gap-2">
        <span className="text-sm">Tasa de conversión</span>
        <Tooltip>
          <TooltipTrigger asChild>
            <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
          </TooltipTrigger>
          <TooltipContent>
            <p>Porcentaje de leads que confirmaron un turno en los últimos 30 días</p>
          </TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  ),
};

export const EnBoton: Story = {
  name: "En botón ícono",
  render: () => (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button size="icon" variant="outline" aria-label="Exportar reporte">
            <Info className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>Exportar reporte a CSV</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  ),
};
