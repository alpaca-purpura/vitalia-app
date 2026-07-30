import type { Meta, StoryObj } from "@storybook/nextjs";
import { toast } from "sonner";

import { Toaster } from "../src/sonner";
import { Button } from "../src/button";

const meta = {
  title: "Molecules/Sonner",
  component: Toaster,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Toaster` (Sonner) es el sistema de notificaciones tipo toast: mensajes transitorios de éxito, error, advertencia o información que no interrumpen el flujo. Úsalo para confirmar acciones (cita guardada, perfil actualizado), notificar errores de red recuperables, o mostrar progreso de operaciones en segundo plano.",
          "",
          "`Toaster` se monta UNA sola vez en el layout raíz. Los toasts se disparan con `import { toast } from \"sonner\"` desde cualquier componente.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Confirmación de acción destructiva** → usa `AlertDialog` (el toast desaparece y el usuario no puede reaccionar a tiempo).",
          "- **Formulario con errores de validación** → usa `FormMessage` al lado del campo.",
          "- **Estado persistente de alerta** → usa `Alert` (permanece visible hasta que el usuario actúa).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Toaster>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  name: "Disparar toasts interactivos",
  render: () => (
    <div className="flex flex-wrap gap-3">
      <Toaster />
      <Button onClick={() => toast.success("Cita guardada correctamente")}>
        Éxito
      </Button>
      <Button
        variant="destructive"
        onClick={() => toast.error("No se pudo actualizar el perfil del paciente")}
      >
        Error
      </Button>
      <Button
        variant="outline"
        onClick={() => toast.warning("La consulta se superpone con otra cita")}
      >
        Advertencia
      </Button>
      <Button
        variant="outline"
        onClick={() => toast.info("El turno fue re-agendado por el paciente")}
      >
        Info
      </Button>
      <Button
        variant="outline"
        onClick={() =>
          toast.loading("Sincronizando agenda con Google Calendar...", {
            duration: 3000,
          })
        }
      >
        Cargando
      </Button>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          "Haz clic en cada botón para ver el toast correspondiente. `Toaster` se monta una sola vez en el layout; los `toast.*()` se invocan desde cualquier componente.",
      },
    },
  },
};

export const ConAccion: Story = {
  name: "Toast con acción",
  render: () => (
    <div>
      <Toaster />
      <Button
        onClick={() =>
          toast("Paciente archivado", {
            description: "El paciente fue movido al archivo.",
            action: {
              label: "Deshacer",
              onClick: () => toast.success("Acción deshecha"),
            },
          })
        }
      >
        Archivar paciente
      </Button>
    </div>
  ),
};
