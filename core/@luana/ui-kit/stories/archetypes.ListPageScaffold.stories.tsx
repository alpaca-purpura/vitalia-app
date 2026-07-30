import type { Meta, StoryObj } from "@storybook/nextjs";
import { CalendarX2, Plus } from "lucide-react";

import { ListPageScaffold } from "../src/archetypes/ListPageScaffold";
import { PageHeader } from "../src/layout/page";
import { FilterBar } from "../src/layout/toolbar";
import { EmptyState } from "../src/layout/states";
import { Pagination } from "../src/layout/pagination";
import { Button } from "../src/button";
import { EntityInfoCard } from "../src/EntityInfoCard";

const mockDoctors = [
  { id: "1", name: "Dra. Lucía Fernández", initials: "LF", subtitle: "Cardiología · Lun a Vie" },
  { id: "2", name: "Dr. Martín Rosas", initials: "MR", subtitle: "Pediatría · Mar a Sab" },
  { id: "3", name: "Dra. Paula Herrera", initials: "PH", subtitle: "Dermatología · Lun Mié Vie" },
  { id: "4", name: "Dr. Carlos Ibáñez", initials: "CI", subtitle: "Traumatología · Lun a Jue" },
  { id: "5", name: "Dra. Sofía Vargas", initials: "SV", subtitle: "Ginecología · Mar Jue Sab" },
  { id: "6", name: "Dr. Diego Méndez", initials: "DM", subtitle: "Oncología · Mié a Vie" },
];

const toolbar = (
  <FilterBar
    search={
      <input
        type="search"
        placeholder="Buscar doctor…"
        className="h-9 w-48 rounded-md border border-input bg-background px-3 text-sm outline-none"
      />
    }
  />
);

const header = (
  <PageHeader
    title="Doctores"
    subtitle={`${mockDoctors.length} especialistas activos`}
    actions={
      <Button size="sm">
        <Plus className="mr-1.5 h-4 w-4" aria-hidden />
        Agregar
      </Button>
    }
  />
);

const meta = {
  title: "Templates/Archetypes/ListPageScaffold",
  component: ListPageScaffold,
  tags: ["autodocs"],
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es el **scaffold de la hoja-lista canónica**. Arma `PageHeader` + `Toolbar/FilterBar` + grilla de `EntityInfoCard` + estados (cargando / vacío / error) + paginación opcional, en la estructura correcta sin que cada feature lo ensamble de cero.",
          "",
          "Úsalo siempre que una hoja sea «mostrar una colección de entidades en grilla»: doctores, pacientes, clínicas, servicios, leads, campañas.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** lo uses si la hoja combina lista + detalle en 1 panel URL-driven — ese patrón es `EntityWorkspaceLayout`.",
          "- **No** lo uses para hojas de formulario (eso es `FormPageScaffold`) ni de dashboard (eso es `DashboardPageScaffold`).",
          "- **No** armes la misma estructura a mano (header + grilla + estados) — eso es lo que este scaffold elimina.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof ListPageScaffold>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ConContenido: Story = {
  name: "Con contenido",
  args: {
    header,
    toolbar,
    children: mockDoctors.map((d) => (
      <EntityInfoCard
        key={d.id}
        title={d.name}
        initials={d.initials}
        subtitle={d.subtitle}
        onClick={() => {}}
      />
    )),
    pagination: <Pagination page={1} pageCount={3} onPrev={() => {}} onNext={() => {}} />,
  },
};

export const Cargando: Story = {
  args: {
    header,
    toolbar,
    isLoading: true,
  },
};

export const Vacio: Story = {
  name: "Vacío",
  args: {
    header,
    toolbar,
    isEmpty: true,
    emptyState: (
      <EmptyState
        icon={<CalendarX2 />}
        title="Sin doctores registrados"
        description="Agrega el primer médico para comenzar a gestionar turnos."
        action={<Button size="sm">Agregar primer doctor</Button>}
      />
    ),
  },
};

export const ConError: Story = {
  name: "Error de carga",
  args: {
    header,
    error: true,
  },
};
