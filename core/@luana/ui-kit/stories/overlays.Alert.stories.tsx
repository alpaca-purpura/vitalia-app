import type { Meta, StoryObj } from "@storybook/nextjs";
import { AlertCircle, CheckCircle2, Info } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "../src/alert";

const meta = {
  title: "Molecules/Alert",
  component: Alert,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Alert` es un mensaje **inline** dentro del contenido de la página: errores de validación globales, advertencias de configuración incompleta, información contextual sobre el estado actual. No interrumpe el flujo (a diferencia del `AlertDialog`).",
          "",
          "Variantes: `default` (informativo) y `destructive` (error/advertencia crítica).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Confirmación antes de una acción irreversible** → usa `AlertDialog` (modal blocking con botones de acción).",
          "- **Notificación de éxito/error post-acción** → usa el sistema de toasts (`Sonner`).",
          "- **Mensaje de carga** → usa el componente `Skeleton` o un spinner.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Alert>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Informativo: Story = {
  render: () => (
    <Alert className="max-w-lg">
      <Info className="h-4 w-4" />
      <AlertTitle>Recordatorio de consentimiento</AlertTitle>
      <AlertDescription>
        Este paciente no tiene consentimiento informado firmado para este tipo de estudio.
        Asegúrate de obtenerlo antes de la consulta.
      </AlertDescription>
    </Alert>
  ),
};

export const Destructivo: Story = {
  name: "Destructivo / Error",
  render: () => (
    <Alert variant="destructive" className="max-w-lg">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Error al guardar</AlertTitle>
      <AlertDescription>
        No se pudo guardar la configuración. Verifica tu conexión e inténtalo de nuevo.
      </AlertDescription>
    </Alert>
  ),
};

export const Exito: Story = {
  name: "Éxito (con ícono verde)",
  render: () => (
    <Alert className="max-w-lg border-green-200 bg-green-50 text-green-900">
      <CheckCircle2 className="h-4 w-4 text-green-600" />
      <AlertTitle>Configuración guardada</AlertTitle>
      <AlertDescription className="text-green-800">
        Los cambios en el perfil del profesional se aplicarán en el próximo turno.
      </AlertDescription>
    </Alert>
  ),
  parameters: {
    docs: {
      description: {
        story:
          "Para éxito, se aplican tokens de color mediante clases Tailwind sobre el `Alert` base. Alternativa preferida post-acción: `Sonner` toast.",
      },
    },
  },
};
