import type { Meta, StoryObj } from "@storybook/nextjs";
import { Search, SlidersHorizontal, LayoutGrid, List } from "lucide-react";

import { Toolbar, FilterBar } from "../src/layout/toolbar";
import { Button } from "../src/button";

const SearchInput = () => (
  <div className="relative">
    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" aria-hidden />
    <input
      type="search"
      placeholder="Buscar doctor…"
      className="h-9 w-56 rounded-md border border-input bg-background pl-8 pr-3 text-sm outline-none focus:ring-2 focus:ring-ring"
    />
  </div>
);

const meta = {
  title: "Templates/Toolbar",
  component: Toolbar,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Toolbar` es la **barra horizontal de acciones** de una hoja de lista: búsqueda, toggles de vista, filtros rápidos. Se posiciona debajo del `<PageHeader>` y encima de la grilla de contenido.",
          "",
          "`FilterBar` es una variante pre-configurada de `Toolbar` que divide el espacio en dos secciones: búsqueda a la izquierda (slot `search`) y orden/modo de vista a la derecha (slots `sort` + `viewMode`). Usa `FilterBar` cuando tengas los dos extremos llenados; usa `Toolbar` cuando el layout sea más libre.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** la uses para las acciones principales de la hoja (ej. «Nuevo doctor») — esas van en el slot `actions` de `<PageHeader>`.",
          "- **No** la uses como barra de acciones flotante — eso es un patrón distinto.",
          "- Si la barra solo tiene un elemento de búsqueda sin filtros, puedes poner el `<input>` directamente sin envolver en `Toolbar`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Toolbar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Basica: Story = {
  name: "Toolbar básica",
  args: {
    children: (
      <>
        <SearchInput />
        <Button variant="outline" size="sm">
          <SlidersHorizontal className="mr-1.5 h-4 w-4" aria-hidden />
          Filtros
        </Button>
      </>
    ),
  },
};

export const ConBarraFiltros: Story = {
  name: "FilterBar (búsqueda + vista)",
  render: () => (
    <FilterBar
      search={<SearchInput />}
      sort={
        <Button variant="outline" size="sm">
          <SlidersHorizontal className="mr-1.5 h-4 w-4" aria-hidden />
          Ordenar
        </Button>
      }
      viewMode={
        <div className="flex rounded-md border border-input">
          <Button variant="ghost" size="icon" className="h-9 w-9 rounded-none rounded-l-md">
            <LayoutGrid className="h-4 w-4" aria-label="Vista grilla" />
          </Button>
          <Button variant="ghost" size="icon" className="h-9 w-9 rounded-none rounded-r-md">
            <List className="h-4 w-4" aria-label="Vista lista" />
          </Button>
        </div>
      }
    />
  ),
  parameters: {
    docs: {
      description: {
        story:
          "`FilterBar` divide la barra en dos extremos. Búsqueda + filtros a la izquierda; orden + toggle de vista a la derecha.",
      },
    },
  },
};
