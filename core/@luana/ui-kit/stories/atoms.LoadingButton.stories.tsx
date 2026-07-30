import type { Meta, StoryObj } from "@storybook/nextjs";

import { LoadingButton } from "../src/loading-button";

const meta = {
  title: "Atoms/LoadingButton",
  component: LoadingButton,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`LoadingButton` extiende `Button` con un estado de carga inline: muestra un spinner (Loader2) y deshabilita el botón mientras `loading={true}`. Úsalo para acciones asíncronas donde el usuario debe esperar una respuesta: guardar formularios, confirmar pagos, enviar invitaciones.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Carga de página completa o datos** → usa `Skeleton` (no un botón).",
          "- **Progreso con porcentaje** → usa `Progress` acompañando al botón.",
          "- **El estado de carga es de otro componente, no del botón** → desvincula el spinner del botón.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof LoadingButton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => <LoadingButton>Guardar cambios</LoadingButton>,
};

export const Cargando: Story = {
  name: "En estado de carga",
  render: () => (
    <LoadingButton loading loadingText="Guardando...">
      Guardar cambios
    </LoadingButton>
  ),
};

export const CargandoSinTexto: Story = {
  name: "Cargando sin texto alternativo",
  render: () => (
    <LoadingButton loading>
      Confirmar cita
    </LoadingButton>
  ),
};

export const Variantes: Story = {
  name: "Variantes",
  render: () => (
    <div className="flex flex-wrap gap-3">
      <LoadingButton loading loadingText="Procesando...">
        Pagar ARS 12.500
      </LoadingButton>
      <LoadingButton variant="outline" loading loadingText="Enviando...">
        Enviar invitación
      </LoadingButton>
      <LoadingButton variant="destructive" loading loadingText="Eliminando...">
        Eliminar registro
      </LoadingButton>
    </div>
  ),
};

export const Deshabilitado: Story = {
  name: "Deshabilitado (sin loading)",
  render: () => (
    <LoadingButton disabled>
      Guardar cambios
    </LoadingButton>
  ),
};
