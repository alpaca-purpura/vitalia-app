import type { Meta, StoryObj } from "@storybook/nextjs";
import { CalendarX2, UserPlus } from "lucide-react";

import { EmptyState, ErrorState } from "../src/layout/states";
import { Button } from "../src/button";

const meta = {
  title: "Templates/EmptyState",
  component: EmptyState,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`EmptyState` es el estado vacío canónico: se muestra cuando una colección existe pero aún no tiene elementos. Combina ícono contextual + mensaje claro + CTA opcional para guiar al usuario a agregar el primer elemento.",
          "",
          "`ErrorState` es el estado de error: se muestra cuando la carga falló. Incluye `role=\"alert\"` para accesibilidad + botón de «Reintentar» opcional.",
          "",
          "Ambos son renderizados por los scaffolds (`ListPageScaffold`, `DashboardPageScaffold`) en sus props `emptyState` y `error`, pero también puedes usarlos de forma independiente dentro de cualquier sección de la hoja.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** los uses para «cargando» — eso es `<ListPageSkeleton>` o `<FormPageSkeleton>`.",
          "- **No** uses `EmptyState` para errores — diferenciá semánticamente: vacío = oportunidad (CTA), error = problema (Reintentar).",
          "- **No** los uses dentro de un `<Group>` de formulario — los errores de campo van inline junto al campo.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof EmptyState>;

export default meta;
type Story = StoryObj<typeof meta>;

export const SinIcono: Story = {
  args: {
    title: "Sin citas programadas",
    description: "Cuando programes citas, aparecerán aquí.",
  },
};

export const ConIcono: Story = {
  args: {
    icon: <CalendarX2 />,
    title: "Sin citas programadas",
    description: "Cuando programes citas, aparecerán aquí.",
    action: (
      <Button size="sm">
        <UserPlus className="mr-1.5 h-4 w-4" aria-hidden />
        Programar primera cita
      </Button>
    ),
  },
};

export const ErrorStateDefault: Story = {
  name: "ErrorState (carga falló)",
  render: () => (
    <ErrorState
      message="No se pudo cargar la lista de doctores. Verifica tu conexión e intenta de nuevo."
      onRetry={() => {}}
    />
  ),
  parameters: {
    docs: {
      description: {
        story:
          "`ErrorState` incluye `role=\"alert\"` y `onRetry` opcional. El texto de acción es editable via `retryLabel`.",
      },
    },
  },
};

export const ErrorStateSinRetry: Story = {
  name: "ErrorState sin reintentar",
  render: () => (
    <ErrorState
      title="No tienes permisos"
      message="Contacta al administrador de la clínica para obtener acceso."
    />
  ),
};
