import type { Meta, StoryObj } from "@storybook/nextjs";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "../src/alert-dialog";
import { Button } from "../src/button";

const meta = {
  title: "Organisms/AlertDialog",
  component: AlertDialog,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`AlertDialog` es el modal de **confirmación de acciones irreversibles o de alto impacto**: eliminar un paciente, cancelar todos los turnos, dar de baja un profesional. El usuario no puede hacer clic fuera para cerrarlo — debe elegir explícitamente confirmar o cancelar.",
          "",
          "El botón de acción principal usa `buttonVariants()` por defecto (se puede personalizar a `destructive`).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Acción reversible o de bajo riesgo** → usa `Dialog` (permite cerrar desde fuera).",
          "- **Mensaje informativo sin decisión requerida** → usa `Alert` inline.",
          "- **Confirmación de un toggle on/off** → un `AlertDialog` puede ser excesivo para switches; considera un tooltip de advertencia.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof AlertDialog>;

export default meta;
type Story = StoryObj<typeof meta>;

// Story clave: AlertDialog ABIERTO
export const Abierto: Story = {
  name: "Abierto — destructivo (revisión directa)",
  render: () => (
    <AlertDialog open>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Eliminar paciente?</AlertDialogTitle>
          <AlertDialogDescription>
            Esta acción no se puede deshacer. Se eliminarán permanentemente el historial de turnos,
            notas clínicas y datos personales del paciente <strong>Valentina Suárez</strong>.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
            Sí, eliminar
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  ),
  parameters: {
    docs: {
      description: {
        story:
          "AlertDialog forzado `open` para revisión directa. Nota: el botón de acción aplica clases destructive manualmente; el `AlertDialogAction` usa `buttonVariants()` base por defecto.",
      },
    },
  },
};

export const ConTrigger: Story = {
  name: "Con trigger interactivo",
  render: () => (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="destructive">Eliminar paciente</Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Confirmar eliminación?</AlertDialogTitle>
          <AlertDialogDescription>
            Esta acción es permanente y no se puede revertir.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
            Eliminar
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  ),
};
