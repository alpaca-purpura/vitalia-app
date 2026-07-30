import type { Meta, StoryObj } from "@storybook/nextjs";

import {
  EntitySubNavBar,
  type EntitySubNavLeaf,
} from "../src/EntitySubNavBar";

/**
 * Story consumes the REAL EntitySubNavBar from src/. It uses next/navigation
 * (useRouter + usePathname) → @storybook/nextjs mocks them (preview: nextjs.appDirectory).
 */
const leaves: EntitySubNavLeaf[] = [
  { id: "ficha", label: "Ficha", href: "/clinica/palermo/ficha", isPrimary: true },
  { id: "agenda", label: "Agenda", href: "/clinica/palermo/agenda" },
  { id: "equipo", label: "Equipo", href: "/clinica/palermo/equipo" },
  { id: "servicios", label: "Servicios", href: "/clinica/palermo/servicios" },
  {
    id: "add",
    label: "Agregar sección",
    href: "#",
    isAddAffordance: true,
  },
];

const meta = {
  title: "Organisms/EntitySubNavBar",
  component: EntitySubNavBar,
  tags: ["autodocs"],
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es la **franja N3 full-bleed** del *detalle* en una vista lista/detalle (canon §2.1-2.2). Aparece cuando el usuario ya eligió una entidad y entró a su workspace. Habla el mismo lenguaje visual que el Ribbon y los SubTabs: `bg-card` + borde inferior + sticky, **nunca** una card redondeada.",
          "",
          "Dos modos en el mismo componente:",
          "- **Master** (`entity = null`): solo el root-pill activo (la lista). El usuario todavía no entró a nada.",
          "- **Workspace** (`entity` seteada): el root-pill `‹ {rootLabel}` con flechita vuelve a la lista; la identidad de la entidad (vía `entityIdentitySlot`, normalmente un `EntityPicker` para cambiar sin volver) + las hojas (`leaves`) + la afordancia de agregar.",
          "",
          "Trae navegación por teclado completa: `role=tablist`, roving `tabindex`, flechas izq/der.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** lo cablees suelto: vive dentro de `EntityWorkspaceLayout`, que decide master vs workspace por la URL y le pasa props.",
          "- **No** lo uses para navegación global de la app (eso es el Ribbon) ni para sub-secciones de una hoja (eso es `SubSubTabsBar`).",
          "- **No** lo metas en una card con borde redondeado — rompe el lenguaje full-bleed del canon.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof EntitySubNavBar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const MasterMode: Story = {
  args: {
    rootHref: "/clinicas",
    rootLabel: "Clínicas",
    entity: null,
    leaves,
    activeLeaf: null,
    placeholder: "Elige una clínica para ver su workspace",
  },
};

export const WorkspaceMode: Story = {
  args: {
    rootHref: "/clinicas",
    rootLabel: "Clínicas",
    entity: { id: "palermo", name: "Sucursal Palermo" },
    leaves,
    activeLeaf: "agenda",
    onAddAffordance: () => {},
  },
};
