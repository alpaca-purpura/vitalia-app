import type { Meta, StoryObj } from "@storybook/nextjs";
import { Calculator, Calendar, User } from "lucide-react";

import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "../src/command";

const meta = {
  title: "Organisms/Command",
  component: Command,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Command` es la paleta de búsqueda + selección rápida del design system (basada en `cmdk`). Úsala para **buscar y navegar entre entidades** cuando la colección es demasiado grande para un `Select`: buscar pacientes por nombre, buscar servicios, acceso rápido a funciones de la app vía shortcut.",
          "",
          "Puede montarse inline (en un Popover o Sheet) o como `CommandDialog` (modal tipo command palette, ej. ⌘K global).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Conjunto cerrado y pequeño (2-20 ítems)** → usa `Select` canónico (más simple y sin infraestructura de búsqueda).",
          "- **Selección de una entidad del sistema (doctores, pacientes)** → `EntityPicker` ya resuelve server-side debounce + paginación cursor + windowed render sobre `Command`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Command>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Command className="rounded-lg border shadow-md w-72">
      <CommandInput placeholder="Buscar paciente, servicio..." />
      <CommandList>
        <CommandEmpty>Sin resultados.</CommandEmpty>
        <CommandGroup heading="Pacientes recientes">
          <CommandItem>
            <User className="mr-2 h-4 w-4" />
            <span>Valentina Suárez</span>
          </CommandItem>
          <CommandItem>
            <User className="mr-2 h-4 w-4" />
            <span>Tomás Figueroa</span>
          </CommandItem>
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Acciones rápidas">
          <CommandItem>
            <Calendar className="mr-2 h-4 w-4" />
            <span>Nuevo turno</span>
            <CommandShortcut>⌘T</CommandShortcut>
          </CommandItem>
          <CommandItem>
            <Calculator className="mr-2 h-4 w-4" />
            <span>Ver agenda del día</span>
            <CommandShortcut>⌘A</CommandShortcut>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </Command>
  ),
};

export const SinResultados: Story = {
  name: "Sin resultados",
  render: () => (
    <Command className="rounded-lg border shadow-md w-72">
      <CommandInput placeholder="Buscar..." defaultValue="xxxx" />
      <CommandList>
        <CommandEmpty>No se encontraron resultados para tu búsqueda.</CommandEmpty>
      </CommandList>
    </Command>
  ),
};
