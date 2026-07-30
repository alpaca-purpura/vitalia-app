import type { Meta, StoryObj } from "@storybook/nextjs";
import { MoreHorizontal, Edit, Trash2, Eye, Copy } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../src/dropdown-menu";
import { Button } from "../src/button";

const meta = {
  title: "Molecules/DropdownMenu",
  component: DropdownMenu,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`DropdownMenu` agrupa un conjunto de **acciones contextuales** que dependen de un elemento específico: editar, duplicar, eliminar, cambiar estado. Se abre desde un trigger (normalmente el botón kebab `⋮` o un chevron).",
          "",
          "Ideal cuando hay 3+ acciones que no entran en la UI visible. Úsalo en tarjetas (`EntityInfoCard` ya lo incluye), filas de tabla, o cabeceras de sección.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Para navegar entre secciones de la app** → usa `Tabs` o `EntitySubNavBar`.",
          "- **Para información de ayuda contextual** → usa `Tooltip` o `Popover`.",
          "- **Para una sola acción** → usa `Button` directamente (no ocultes una acción principal en un menú).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof DropdownMenu>;

export default meta;
type Story = StoryObj<typeof meta>;

// Story clave: menú ABIERTO
export const Abierto: Story = {
  name: "Abierto (revisión directa)",
  render: () => (
    <div className="flex items-start justify-center pt-4">
      <DropdownMenu open>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" aria-label="Acciones">
            <MoreHorizontal />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-44">
          <DropdownMenuLabel>Acciones del turno</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem>
            <Eye className="mr-2 h-4 w-4" />
            Ver detalle
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Edit className="mr-2 h-4 w-4" />
            Editar
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Copy className="mr-2 h-4 w-4" />
            Duplicar
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem className="text-destructive focus:text-destructive">
            <Trash2 className="mr-2 h-4 w-4" />
            Eliminar
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  ),
  parameters: {
    layout: "padded",
    docs: {
      description: {
        story:
          "Menú forzado `open` para revisión directa. Muestra acciones típicas de un turno con separador antes de la acción destructiva.",
      },
    },
  },
};

export const ConTrigger: Story = {
  name: "Con trigger interactivo",
  render: () => (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Más acciones">
          <MoreHorizontal />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-44">
        <DropdownMenuItem>Ver paciente</DropdownMenuItem>
        <DropdownMenuItem>Reprogramar</DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="text-destructive focus:text-destructive">
          Cancelar turno
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  ),
};
