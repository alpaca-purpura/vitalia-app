import type { Meta, StoryObj } from "@storybook/nextjs";

import { DetailPageScaffold } from "../src/archetypes/DetailPageScaffold";
import { PageHeader } from "../src/layout/page";
import { EntitySubNavBar } from "../src/EntitySubNavBar";

const leaves = [
  { id: "ficha", label: "Ficha", href: "/doctores/fernandez/ficha", isPrimary: true },
  { id: "agenda", label: "Agenda", href: "/doctores/fernandez/agenda" },
  { id: "pacientes", label: "Pacientes", href: "/doctores/fernandez/pacientes" },
];

const subnav = (
  <EntitySubNavBar
    rootHref="/doctores"
    rootLabel="Doctores"
    entityName="Dra. Lucía Fernández"
    leaves={leaves}
    activeLeaf="ficha"
  />
);

const meta = {
  title: "Templates/Archetypes/DetailPageScaffold",
  component: DetailPageScaffold,
  tags: ["autodocs"],
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es el **scaffold de la hoja-detalle canónica**. Arma la franja N3 full-bleed (`EntitySubNavBar`, pasada en el slot `subnav`) + el contenido del leaf activo (envuelto en `DetailLayout`) + estados (cargando / error).",
          "",
          "El scaffold es **router-free**: no lee `next/navigation`. El consumidor monta el `EntitySubNavBar` ya configurado y lo pasa en `subnav`. Así el scaffold permanece testeable sin mocks de router.",
          "",
          "Úsalo para la vista de detalle de cualquier entidad: ficha de doctor, historial de paciente, configuración de servicio.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** lo uses para listas (eso es `ListPageScaffold`) ni formularios independientes (eso es `FormPageScaffold`).",
          "- Si la hoja tiene tabs de navegación propias en lugar de `EntitySubNavBar`, puedes pasar `header` en vez de `subnav`.",
          "- Si la entidad se selecciona desde una grilla lateral, el patrón completo es `EntityWorkspaceLayout` (que ya incluye `DetailPageScaffold` internamente).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof DetailPageScaffold>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ConSubnav: Story = {
  name: "Con EntitySubNavBar (franja N3)",
  args: {
    subnav,
    children: (
      <div className="flex flex-col gap-4">
        <p className="text-base font-medium text-foreground">Dra. Lucía Fernández</p>
        <p className="text-sm text-muted-foreground">Cardiología · Hospital San Martín</p>
        <p className="text-sm text-muted-foreground">
          Contenido del leaf activo «Ficha». El scaffold lo envuelve en{" "}
          <code>DetailLayout</code> (max-w-3xl).
        </p>
      </div>
    ),
  },
};

export const ConHeader: Story = {
  name: "Con PageHeader (sin EntitySubNavBar)",
  args: {
    header: (
      <PageHeader
        title="Configuración del servicio"
        subtitle="Consulta de cardiología"
      />
    ),
    children: (
      <p className="text-sm text-muted-foreground">
        Cuando la hoja no tiene tabs de navegación por leaves, pasá el encabezado en el
        slot <code>header</code> en vez de <code>subnav</code>.
      </p>
    ),
  },
};

export const Cargando: Story = {
  args: {
    subnav,
    isLoading: true,
  },
};

export const ConError: Story = {
  name: "Error de carga",
  args: {
    subnav,
    error: true,
  },
};
