import type { Meta, StoryObj } from "@storybook/nextjs";

import { FormPageScaffold } from "../src/archetypes/FormPageScaffold";
import { PageHeader } from "../src/layout/page";
import { Group, GroupHeader } from "../src/Group";
import { FloatingAutosaveIndicator } from "../src/FloatingAutosaveIndicator";

const header = (
  <PageHeader
    title="Perfil del doctor"
    subtitle="Los cambios se guardan automáticamente"
  />
);

const meta = {
  title: "Templates/Archetypes/FormPageScaffold",
  component: FormPageScaffold,
  tags: ["autodocs"],
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es el **scaffold de la hoja-formulario canónica**. Arma `PageHeader` + `FormLayout` (1 col o 2 col paired) + slot para `<FloatingAutosaveIndicator>` (UNA sola instancia por página, canon §2.6).",
          "",
          "Úsalo para cualquier hoja que contenga campos editables: perfil de entidad, configuración de servicio, datos de campaña.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** lo uses para listas (eso es `ListPageScaffold`) ni para dashboards de lectura (eso es `DashboardPageScaffold`).",
          "- **No** uses `paired={true}` por defecto — solo cuando los campos forman pares conceptuales (ej. Nombre + Apellido).",
          "- El slot `autosaveIndicator` recibe **una sola** `<FloatingAutosaveIndicator>`. No pongas un `AutosaveBadge` por grupo además del indicador flotante global.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof FormPageScaffold>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ConContenido: Story = {
  name: "Con grupos de campos",
  args: {
    header,
    children: (
      <>
        <Group>
          <GroupHeader title="Datos profesionales" whatFor="Para Lisa" />
          <div className="grid gap-3">
            <div className="h-9 rounded-md border border-input bg-background" />
            <div className="h-9 rounded-md border border-input bg-background" />
          </div>
        </Group>
        <Group>
          <GroupHeader title="Horarios de atención" whatFor="Para la agenda" />
          <div className="grid gap-3">
            <div className="h-9 rounded-md border border-input bg-background" />
          </div>
        </Group>
      </>
    ),
    autosaveIndicator: <FloatingAutosaveIndicator status="saved" savedAt={new Date()} />,
  },
};

export const Cargando: Story = {
  args: {
    header,
    isLoading: true,
  },
};

export const EstadoGuardando: Story = {
  name: "Guardando (autosave en curso)",
  args: {
    header,
    children: (
      <Group>
        <GroupHeader title="Datos profesionales" />
        <div className="h-9 rounded-md border border-input bg-background" />
      </Group>
    ),
    autosaveIndicator: <FloatingAutosaveIndicator status="saving" />,
  },
};

export const EstadoError: Story = {
  name: "Error al guardar",
  args: {
    header,
    children: (
      <Group>
        <GroupHeader title="Datos profesionales" />
        <div className="h-9 rounded-md border border-input bg-background" />
      </Group>
    ),
    autosaveIndicator: <FloatingAutosaveIndicator status="error" />,
  },
};
