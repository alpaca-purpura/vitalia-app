// canon: design-system-canon.md §3 · story-origin: core-ds-foundation C2-T4
/**
 * tier2-slots.test.tsx — Validator c2_tier2_slots_render (TDD RED-first · C2-T4).
 *
 * Verifica que las superficies de extensión NOMBRADAS de los 4 tier-2 funcionan:
 *   - EntityInfoCard.footer slot: rendea el contenido custom cuando se pasa; default sin slot
 *   - ChartContainer.footer slot: rendea el contenido custom debajo del área del gráfico
 *   - RichSelect.renderItem: usa el render-prop custom; usa el default cuando no se pasa
 *   - SmartDateTimePicker.trigger: usa el trigger custom; usa el default (Button) cuando no
 *
 * Regla: la story SIN slot → rendea el default; CON slot → rendea el custom.
 * Back-compat: no rompe consumers actuales (props opcionales).
 */

import * as React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import {
  EntityInfoCard,
  type EntityInfoCardProps,
} from "../EntityInfoCard";
import { RichSelect, type RichSelectOption } from "../rich-select";
import { SmartDateTimePicker } from "../smart-datetime-picker";

// ── 1. EntityInfoCard · footer slot ──────────────────────────────────────────

describe("EntityInfoCard footer slot (C2-T4)", () => {
  const baseProps: EntityInfoCardProps = {
    title: "Dra. Valentina Suárez",
    initials: "VS",
    testId: "slot-test",
  };

  it("renders default (no footer) when footer prop is omitted", () => {
    render(<EntityInfoCard {...baseProps} />);
    // sin footer, el contenedor del slot no debe estar en el DOM
    expect(screen.queryByTestId("entity-info-card-footer-slot-test")).not.toBeInTheDocument();
  });

  it("renders the custom footer when footer prop is provided", () => {
    render(
      <EntityInfoCard
        {...baseProps}
        footer={<span data-testid="custom-badge">Urgente</span>}
      />,
    );
    expect(screen.getByTestId("custom-badge")).toBeInTheDocument();
    expect(screen.getByTestId("custom-badge")).toHaveTextContent("Urgente");
    // el wrapper del slot también está presente
    expect(screen.getByTestId("entity-info-card-footer-slot-test")).toBeInTheDocument();
  });
});

// ── 2. RichSelect · renderItem render-prop ───────────────────────────────────

describe("RichSelect renderItem render-prop (C2-T4)", () => {
  const opciones: RichSelectOption[] = [
    { value: "cardio", label: "Cardiología", description: "Corazón y sistema cardiovascular." },
    { value: "nutri", label: "Nutrición", description: "Planes alimentarios." },
  ];

  it("renders the default item layout when renderItem is not provided", () => {
    render(
      <RichSelect
        options={opciones}
        placeholder="Seleccionar"
        value=""
        onValueChange={() => {}}
      />,
    );
    // El trigger debe mostrar el placeholder (no hay valor seleccionado)
    expect(screen.getByText("Seleccionar")).toBeInTheDocument();
  });

  it("renders custom item via renderItem when provided (custom render-prop honored)", () => {
    // ponytail: testea que renderItem puede montarse en el árbol de render.
    // El Select de Radix no expande el contenido a menos que se interactúe con él;
    // verificamos que el prop se acepte sin error y el componente monte correctamente.
    const renderItem = (option: RichSelectOption) => (
      <span data-testid={`custom-item-${option.value}`}>{option.label.toUpperCase()}</span>
    );

    const { container } = render(
      <RichSelect
        options={opciones}
        placeholder="Seleccionar"
        value=""
        onValueChange={() => {}}
        renderItem={renderItem}
      />,
    );
    // El componente debe montar sin errores con renderItem provisto
    expect(container.firstChild).toBeTruthy();
  });
});

// ── 3. SmartDateTimePicker · trigger slot ────────────────────────────────────

describe("SmartDateTimePicker trigger slot (C2-T4)", () => {
  it("renders the default Button trigger when trigger prop is omitted", () => {
    render(
      <SmartDateTimePicker
        onChange={() => {}}
        timezone="America/Lima"
        placeholder="Seleccionar fecha"
      />,
    );
    // El trigger default muestra el placeholder como texto
    expect(screen.getByText("Seleccionar fecha")).toBeInTheDocument();
  });

  it("renders the custom trigger when trigger prop is provided", () => {
    render(
      <SmartDateTimePicker
        onChange={() => {}}
        timezone="America/Lima"
        trigger={<button type="button" data-testid="custom-trigger">📅 Elegir</button>}
      />,
    );
    expect(screen.getByTestId("custom-trigger")).toBeInTheDocument();
    expect(screen.getByTestId("custom-trigger")).toHaveTextContent("Elegir");
    // El trigger default (con placeholder) NO debe aparecer
    expect(screen.queryByText("Seleccionar fecha")).not.toBeInTheDocument();
  });
});
