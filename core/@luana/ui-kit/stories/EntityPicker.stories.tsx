import * as React from "react";
import type { Meta, StoryObj } from "@storybook/nextjs";

import {
  EntityPicker,
  type EntityPickerItem,
  type EntitySearchFn,
} from "../src/EntityPicker";

/**
 * Story consumes the REAL EntityPicker from src/. The component is query-lib agnostic:
 * it takes a `searchFn` (debounced, server-side search + cursor pagination) and renders
 * results windowed (react-virtual). No react-query / QueryClientProvider needed — the
 * story supplies a mock async searchFn over realistic LatAm doctor data.
 */
const DOCTORS: EntityPickerItem[] = [
  { id: "d-001", name: "Dra. Valentina Suárez", initials: "VS" },
  { id: "d-002", name: "Dr. Tomás Figueroa", initials: "TF" },
  { id: "d-003", name: "Dra. Camila Restrepo", initials: "CR" },
  { id: "d-004", name: "Dr. Mateo Quispe", initials: "MQ" },
  { id: "d-005", name: "Dra. Renata Ávila", initials: "RA" },
  { id: "d-006", name: "Dr. Joaquín Morales", initials: "JM" },
  { id: "d-007", name: "Dra. Isabella Cárdenas", initials: "IC" },
  { id: "d-008", name: "Dr. Benjamín Rojas", initials: "BR" },
  { id: "d-009", name: "Dra. Antonella Vega", initials: "AV" },
  { id: "d-010", name: "Dr. Facundo Herrera", initials: "FH" },
  { id: "d-011", name: "Dra. Martina Ocampo", initials: "MO" },
  { id: "d-012", name: "Dr. Lautaro Bustos", initials: "LB" },
  { id: "d-013", name: "Dra. Emilia Paredes", initials: "EP" },
  { id: "d-014", name: "Dr. Santiago Fuentes", initials: "SF" },
  { id: "d-015", name: "Dra. Catalina Ñañez", initials: "CÑ" },
];

const PAGE = 6;

/** Mock server: filters by q, then returns a cursor-paged slice (simulated latency). */
const searchFn: EntitySearchFn<EntityPickerItem> = async ({ q, cursor, limit }) => {
  await new Promise((r) => setTimeout(r, 180));
  const filtered = q
    ? DOCTORS.filter((d) => d.name.toLowerCase().includes(q.toLowerCase()))
    : DOCTORS;
  const start = cursor ? Number(cursor) : 0;
  const size = limit ?? PAGE;
  const items = filtered.slice(start, start + size);
  const next = start + size;
  return {
    items,
    nextCursor: next < filtered.length ? String(next) : undefined,
    total: filtered.length,
  };
};

const meta = {
  title: "Organisms/EntityPicker",
  component: EntityPicker,
  tags: ["autodocs"],
  // Meta-level default satisfies the required `searchFn` for every story; the
  // interactive wrapper (render) owns value/onChange state.
  args: { searchFn },
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es el **selector de entidad con búsqueda server-side** (canon §2.4). Úsalo cuando el usuario debe elegir una entre **muchas** (cientos/miles): el doctor de un turno, la clínica activa, el paciente de un registro. Busca con debounce, pide páginas por cursor y **renderiza windowed** — nunca carga la colección entera al cliente.",
          "",
          "Su lugar estrella es la identidad del workspace en `EntitySubNavBar` (el `▾` que cambia de entidad sin volver a la lista).",
          "",
          "Es agnóstico de librería de datos: recibe un `searchFn(args) => Promise<{items, nextCursor?, total?}>`. De dónde salgan esos datos (React Query, fetch directo, lo que sea) es problema de quien lo usa, no del componente.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** lo uses para 3-10 opciones fijas conocidas → ahí va el `Select` canónico (canon §2.5).",
          "- **No** cargues toda la colección al cliente para filtrar en memoria — el contrato es búsqueda + paginación en el servidor.",
          "- **No** uses un `<select>` nativo para colecciones grandes: pierde búsqueda, paginación y windowing.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof EntityPicker<EntityPickerItem>>;

export default meta;
type Story = StoryObj<typeof meta>;

const Interactive = (
  args: Partial<React.ComponentProps<typeof EntityPicker<EntityPickerItem>>>,
) => {
  const [value, setValue] = React.useState<EntityPickerItem | null>(null);
  return (
    <div className="w-80">
      <EntityPicker
        searchFn={searchFn}
        value={value}
        onChange={setValue}
        limit={PAGE}
        placeholder="Seleccionar profesional…"
        searchPlaceholder="Buscar por nombre…"
        emptyLabel="Sin profesionales que coincidan"
        {...args}
      />
    </div>
  );
};

export const Default: Story = {
  render: () => <Interactive />,
};

export const Preselected: Story = {
  render: () => <Interactive />,
  parameters: {
    docs: {
      description: {
        story:
          "Abre el selector y busca: el footer muestra \"Mostrando N de M\" mientras pagina por cursor.",
      },
    },
  },
};

export const Disabled: Story = {
  render: () => <Interactive disabled />,
};

export const WithCreateAction: Story = {
  name: "Con acción de crear (pick-or-create)",
  render: () => (
    <Interactive
      placeholder="Seleccionar servicio…"
      searchPlaceholder="Buscar o crear servicio…"
      emptyLabel="Sin servicios que coincidan"
      createAction={{
        label: (q) => `Crear «${q}»`,
        onCreate: (q) => window.alert(`Crear servicio: ${q}`),
      }}
    />
  ),
  parameters: {
    docs: {
      description: {
        story:
          "Patrón **pick-or-create**: escribe algo que no exista (ej. «Limpieza dental») y aparece una fila final `＋ Crear «…»` (borde superior punteado) que dispara `onCreate(query)`. Es aditivo — sin `createAction` el selector se comporta igual que siempre. La fila es navegable por teclado (↓ hasta ella, Enter para crear).",
      },
    },
  },
};
