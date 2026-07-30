import type { Meta, StoryObj } from "@storybook/nextjs";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  type ChartConfig,
} from "../src/chart";

const meta = {
  title: "Organisms/Chart",
  component: ChartContainer,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`ChartContainer` envuelve gráficas de Recharts con tokens de color del design system, tooltip estandarizado (`ChartTooltipContent`) y leyenda (`ChartLegendContent`). Úsalo en el Growth Studio para visualizar embudos de conversión, evolución de métricas de atracción/venta, o comparativas de canales por período.",
          "",
          "La configuración `ChartConfig` declara las series con sus colores semánticos (`var(--color-*)` generados automáticamente); el consumer nunca usa hex ni colores hardcodeados.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Dato único o KPI sin tendencia** → usa una `Card` con número grande.",
          "- **Tabla comparativa exacta** → usa `Table` (los gráficos son para tendencias, no para valores exactos que el usuario necesita copiar).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof ChartContainer>;

export default meta;
type Story = StoryObj<typeof meta>;

const dataMensual = [
  { mes: "Ene", consultas: 42, nuevos: 18 },
  { mes: "Feb", consultas: 55, nuevos: 22 },
  { mes: "Mar", consultas: 48, nuevos: 15 },
  { mes: "Abr", consultas: 63, nuevos: 30 },
  { mes: "May", consultas: 71, nuevos: 27 },
  { mes: "Jun", consultas: 58, nuevos: 21 },
];

const barConfig = {
  consultas: { label: "Consultas totales", color: "hsl(var(--chart-1))" },
  nuevos: { label: "Pacientes nuevos", color: "hsl(var(--chart-2))" },
} satisfies ChartConfig;

export const BarrasMensuales: Story = {
  name: "Barras — consultas mensuales",
  render: () => (
    <ChartContainer config={barConfig} className="h-64 w-full">
      <BarChart data={dataMensual}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="mes" tickLine={false} axisLine={false} />
        <YAxis tickLine={false} axisLine={false} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <ChartLegend content={<ChartLegendContent />} />
        <Bar dataKey="consultas" fill="var(--color-consultas)" radius={4} />
        <Bar dataKey="nuevos" fill="var(--color-nuevos)" radius={4} />
      </BarChart>
    </ChartContainer>
  ),
};

const dataLinea = [
  { semana: "S1", tasa: 62 },
  { semana: "S2", tasa: 68 },
  { semana: "S3", tasa: 71 },
  { semana: "S4", tasa: 65 },
  { semana: "S5", tasa: 78 },
  { semana: "S6", tasa: 82 },
];

const lineConfig = {
  tasa: { label: "Tasa de conversión (%)", color: "hsl(var(--chart-3))" },
} satisfies ChartConfig;

export const LineaTendencia: Story = {
  name: "Línea — tasa de conversión",
  render: () => (
    <ChartContainer config={lineConfig} className="h-64 w-full">
      <LineChart data={dataLinea}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="semana" tickLine={false} axisLine={false} />
        <YAxis tickLine={false} axisLine={false} domain={[50, 100]} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Line
          type="monotone"
          dataKey="tasa"
          stroke="var(--color-tasa)"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ChartContainer>
  ),
};

/** C2-T4 · consumer story — slot `footer` ejercido debajo del área del gráfico. */
export const ConFooterCustom: Story = {
  name: "Con footer custom (C2-T4)",
  render: () => (
    <ChartContainer
      config={barConfig}
      className="h-64 w-full"
      footer={
        <span>
          Fuente: sistema de gestión Vitalia · Período: Ene–Jun 2026 · Actualizado hoy
        </span>
      }
    >
      <BarChart data={dataMensual}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="mes" tickLine={false} axisLine={false} />
        <YAxis tickLine={false} axisLine={false} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar dataKey="consultas" fill="var(--color-consultas)" radius={4} />
      </BarChart>
    </ChartContainer>
  ),
  parameters: {
    docs: {
      description: {
        story:
          "Slot `footer` (C2-T4): texto/nodo custom renderizado debajo del gráfico dentro del mismo `ChartContainer`. Útil para fuente del dato, período, o nota aclaratoria. Sin `footer` → no renderiza nada extra.",
      },
    },
  },
};
