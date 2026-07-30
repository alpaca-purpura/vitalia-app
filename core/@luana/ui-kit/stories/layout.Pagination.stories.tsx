import type { Meta, StoryObj } from "@storybook/nextjs";
import * as React from "react";

import { Pagination } from "../src/layout/pagination";

const meta = {
  title: "Molecules/Pagination",
  component: Pagination,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es la barra de **paginación estándar de lista**: botones «Anterior» / «Siguiente» + indicador «Página X de Y» con `aria-live` para accesibilidad. Se posiciona al pie de una lista o grilla cuando los elementos están divididos en páginas.",
          "",
          "Los botones se deshabilitan automáticamente en los extremos (`page ≤ 1` → deshabilita «Anterior»; `page ≥ pageCount` → deshabilita «Siguiente»).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** la uses para scroll infinito — ese patrón no usa `<Pagination>`, sino un `IntersectionObserver` que carga más registros.",
          "- **No** la uses para navegación de steps en un wizard — usa un indicador de progreso o tabs.",
          "- Si la grilla muestra todos los elementos de una colección pequeña (≤30), no es necesaria.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Pagination>;

export default meta;
type Story = StoryObj<typeof meta>;

export const PrimeraPagina: Story = {
  args: {
    page: 1,
    pageCount: 8,
    onPrev: () => {},
    onNext: () => {},
  },
};

export const PaginaIntermedia: Story = {
  args: {
    page: 4,
    pageCount: 8,
    onPrev: () => {},
    onNext: () => {},
  },
};

export const UltimaPagina: Story = {
  name: "Última página",
  args: {
    page: 8,
    pageCount: 8,
    onPrev: () => {},
    onNext: () => {},
  },
};

export const PaginaUnica: Story = {
  name: "Una sola página (ambos botones deshabilitados)",
  args: {
    page: 1,
    pageCount: 1,
    onPrev: () => {},
    onNext: () => {},
  },
};

export const Interactiva: Story = {
  name: "Interactiva (estado local)",
  render: () => {
    const [page, setPage] = React.useState(1);
    const total = 5;
    return (
      <Pagination
        page={page}
        pageCount={total}
        onPrev={() => setPage((p) => Math.max(1, p - 1))}
        onNext={() => setPage((p) => Math.min(total, p + 1))}
      />
    );
  },
  parameters: {
    docs: {
      description: {
        story: "Versión interactiva con estado local para explorar los extremos en Storybook.",
      },
    },
  },
};
