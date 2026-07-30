import type { Meta, StoryObj } from "@storybook/nextjs";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../src/dialog";
import { Button } from "../src/button";
import { Input } from "../src/input";
import { Label } from "../src/label";

const meta = {
  title: "Organisms/Dialog",
  component: Dialog,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Dialog` es el modal **blocking** del design system: interrumpe el flujo para una acción que requiere atención completa del usuario. Úsalo para formularios cortos de creación (nuevo paciente, nueva especialidad), edición de un campo crítico, o confirmación de una acción no destructiva.",
          "",
          "La `DialogContent` es portal — se monta sobre toda la UI, respeta el offset del copilot lateral.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Acción destructiva irreversible** (eliminar, dar de baja) → usa `AlertDialog` (tiene variante destructiva con semántica de advertencia).",
          "- **Formulario largo o multistep** → usa `Sheet` (panel lateral, más espacio y menos claustrofóbico).",
          "- **Información contextual de un elemento** → usa `Popover` (no interrumpe el flujo).",
          "- **Mensaje de éxito/error** → usa el sistema de toasts (`Sonner`), no un Dialog.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Dialog>;

export default meta;
type Story = StoryObj<typeof meta>;

// Story clave: dialog ABIERTO para revisión
export const Abierto: Story = {
  name: "Abierto (revisión directa)",
  render: () => (
    <Dialog open>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Agregar profesional</DialogTitle>
          <DialogDescription>
            Completa los datos básicos. Podrás editar el perfil completo después.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-1.5">
            <Label htmlFor="pro-name">Nombre completo</Label>
            <Input id="pro-name" placeholder="Dra. Valentina Suárez" />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="pro-specialty">Especialidad</Label>
            <Input id="pro-specialty" placeholder="Cardiología" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline">Cancelar</Button>
          <Button>Agregar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
  parameters: {
    docs: {
      description: {
        story:
          "Dialog renderizado con `open` para revisión inmediata en el canvas. En producción el trigger abre el modal.",
      },
    },
  },
};

export const ConTrigger: Story = {
  name: "Con trigger interactivo",
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Agregar profesional</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Agregar profesional</DialogTitle>
          <DialogDescription>
            Completa los datos básicos del nuevo miembro del equipo.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-1.5">
            <Label htmlFor="dg-name">Nombre completo</Label>
            <Input id="dg-name" placeholder="Dra. Valentina Suárez" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline">Cancelar</Button>
          <Button>Agregar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
};
