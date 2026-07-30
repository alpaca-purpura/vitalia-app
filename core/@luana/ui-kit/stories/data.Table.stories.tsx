import type { Meta, StoryObj } from "@storybook/nextjs";

import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../src/table";
import { Badge } from "../src/badge";

const meta = {
  title: "Organisms/Table",
  component: Table,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Table` es para datos tabulares estructurados: lista de citas con fecha/hora/paciente/estado, historial de pagos, comparativa de métricas por canal. Cada fila es una entidad con múltiples atributos que el usuario necesita comparar horizontalmente.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Lista de entidades navegables** → usa `EntityInfoCard` en grid (canon §2.3); las tablas no son el destino de navegación principal.",
          "- **Una sola columna** → usa una lista (`ul`) o tarjetas; la tabla agrega complejidad innecesaria.",
          "- **Datos anidados complejos** → descompón en múltiples vistas o usa un `Accordion`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Table>;

export default meta;
type Story = StoryObj<typeof meta>;

const citas = [
  { id: "C-001", paciente: "Lucía Méndez", especialidad: "Cardiología", fecha: "22/06/2026 09:00", monto: "ARS 8.500", estado: "confirmada" },
  { id: "C-002", paciente: "Roberto Pérez", especialidad: "Nutrición", fecha: "22/06/2026 10:30", monto: "ARS 6.000", estado: "pendiente" },
  { id: "C-003", paciente: "Fernanda Ríos", especialidad: "Psicología", fecha: "22/06/2026 12:00", monto: "ARS 7.200", estado: "confirmada" },
  { id: "C-004", paciente: "Carlos Díaz", especialidad: "Cardiología", fecha: "23/06/2026 08:00", monto: "ARS 8.500", estado: "cancelada" },
];

const estadoVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  confirmada: "default",
  pendiente: "secondary",
  cancelada: "destructive",
};

export const Default: Story = {
  render: () => (
    <Table>
      <TableCaption>Citas del día — Dr. Martín Alvarado</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>ID</TableHead>
          <TableHead>Paciente</TableHead>
          <TableHead>Especialidad</TableHead>
          <TableHead>Fecha y hora</TableHead>
          <TableHead>Monto</TableHead>
          <TableHead>Estado</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {citas.map((cita) => (
          <TableRow key={cita.id}>
            <TableCell className="font-mono text-xs text-muted-foreground">{cita.id}</TableCell>
            <TableCell>{cita.paciente}</TableCell>
            <TableCell>{cita.especialidad}</TableCell>
            <TableCell>{cita.fecha}</TableCell>
            <TableCell>{cita.monto}</TableCell>
            <TableCell>
              <Badge variant={estadoVariant[cita.estado]}>{cita.estado}</Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  ),
};

export const Vacia: Story = {
  name: "Estado vacío",
  render: () => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Paciente</TableHead>
          <TableHead>Especialidad</TableHead>
          <TableHead>Estado</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell colSpan={3} className="text-center text-muted-foreground py-8">
            No hay citas para este período.
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ),
};
