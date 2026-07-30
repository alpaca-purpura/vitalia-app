// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * KanbanBoard.test.tsx — RED-first tests for KanbanBoard (T-FE-2).
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { KanbanBoard } from "../KanbanBoard";
import type { BoardColumn } from "../../../types/embudo.types";

vi.mock("@dnd-kit/core", () => ({
  DndContext: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  PointerSensor: vi.fn(),
  KeyboardSensor: vi.fn(),
  useSensor: vi.fn(),
  useSensors: vi.fn(() => []),
  DragOverlay: () => null,
  closestCenter: vi.fn(),
}));

vi.mock("../PipelineColumn", () => ({
  PipelineColumn: ({ column }: { column: BoardColumn }) => (
    <div data-testid={`column-${column.stage}`}>{column.label}</div>
  ),
}));

const MOCK_COLUMNS: BoardColumn[] = [
  { stage: "interesado", label: "Interesado", count: 3, sumValue: 23000, currency: "PEN", overSlaCount: 1, leads: [] },
  { stage: "calificando", label: "Calificando", count: 2, sumValue: 14000, currency: "PEN", overSlaCount: 0, leads: [] },
  { stage: "consulta_agendada", label: "Consulta agendada", count: 1, sumValue: 11000, currency: "PEN", overSlaCount: 0, leads: [] },
  { stage: "plan_presentado", label: "Plan presentado", count: 1, sumValue: 12000, currency: "PEN", overSlaCount: 1, leads: [] },
  { stage: "reservado", label: "Reservado", count: 2, sumValue: 15000, currency: "PEN", overSlaCount: 0, leads: [] },
];

describe("KanbanBoard", () => {
  it("renders all 5 columns (4 active + reservado)", () => {
    render(<KanbanBoard columns={MOCK_COLUMNS} onStageDrop={vi.fn()} activeLeadId={null} />);
    expect(screen.getByTestId("column-interesado")).toBeInTheDocument();
    expect(screen.getByTestId("column-calificando")).toBeInTheDocument();
    expect(screen.getByTestId("column-consulta_agendada")).toBeInTheDocument();
    expect(screen.getByTestId("column-plan_presentado")).toBeInTheDocument();
    expect(screen.getByTestId("column-reservado")).toBeInTheDocument();
  });

  it("renders empty state when no columns provided", () => {
    render(<KanbanBoard columns={[]} onStageDrop={vi.fn()} activeLeadId={null} />);
    expect(document.body).toBeInTheDocument();
  });

  it("has role=region container", () => {
    render(<KanbanBoard columns={MOCK_COLUMNS} onStageDrop={vi.fn()} activeLeadId={null} />);
    expect(screen.getByRole("region", { name: /tablero/i })).toBeInTheDocument();
  });
});
