// canon: design-system-canon.md §2.3 · story-origin: core-ds-foundation
/**
 * EntityInfoCard.test.tsx — Validator F-8 for the canon §2.3 entity card (@luana/ui-kit).
 *
 * Covers:
 *   - whole-card click fires onClick (role=button)
 *   - keyboard activation (Enter / Space) fires onClick
 *   - kebab ⋮ click does NOT fire the card onClick (stopPropagation) + opens menu
 *   - agent-color accent applied (top border accentClass)
 *   - metrics row renders the metrics (values + labels)
 *   - EntityInfoCardSkeleton renders
 *   - EntityInfoCardEmpty renders
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import * as React from "react";

import {
  EntityInfoCard,
  EntityInfoCardSkeleton,
  EntityInfoCardEmpty,
  type EntityCardAction,
} from "../EntityInfoCard";

// ── Fixtures ────────────────────────────────────────────────────────────────

const metrics = [
  { label: "Años exp.", value: "8a" },
  { label: "Pacientes", value: 124 },
  { label: "NPS", value: 92 },
];

function renderCard(props?: Partial<React.ComponentProps<typeof EntityInfoCard>>) {
  return render(
    <EntityInfoCard
      title="Dra. Valentina Ríos"
      subtitle="Odontología cosmética"
      initials="VR"
      accentClass="border-t-agent-lisa"
      metrics={metrics}
      status={{ label: "Activo", variant: "secondary" }}
      testId="doc-1"
      {...props}
    />,
  );
}

// ── Tests ───────────────────────────────────────────────────────────────────

describe("EntityInfoCard", () => {
  it("fires onClick when the whole card is clicked (role=button)", () => {
    const onClick = vi.fn();
    renderCard({ onClick });

    const card = screen.getByTestId("entity-info-card-doc-1");
    expect(card).toHaveAttribute("role", "button");
    expect(card).toHaveAttribute("tabindex", "0");

    fireEvent.click(card);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("activates onClick via keyboard (Enter and Space)", () => {
    const onClick = vi.fn();
    renderCard({ onClick });
    const card = screen.getByTestId("entity-info-card-doc-1");

    fireEvent.keyDown(card, { key: "Enter" });
    fireEvent.keyDown(card, { key: " " });
    expect(onClick).toHaveBeenCalledTimes(2);
  });

  it("does NOT render role=button when there is no onClick", () => {
    renderCard({ onClick: undefined });
    const card = screen.getByTestId("entity-info-card-doc-1");
    expect(card).not.toHaveAttribute("role", "button");
  });

  it("renders the kebab ⋮ trigger only when actions are provided", () => {
    const actions: EntityCardAction[] = [
      { id: "edit", label: "Editar", onSelect: vi.fn() },
      { id: "delete", label: "Eliminar", onSelect: vi.fn(), destructive: true, separatorBefore: true },
    ];
    const { rerender } = renderCard({ actions: undefined });
    expect(screen.queryByTestId("entity-info-card-kebab-doc-1")).not.toBeInTheDocument();

    rerender(
      <EntityInfoCard
        title="Dra. Valentina Ríos"
        subtitle="Odontología cosmética"
        initials="VR"
        accentClass="border-t-agent-lisa"
        metrics={metrics}
        status={{ label: "Activo", variant: "secondary" }}
        testId="doc-1"
        actions={actions}
      />,
    );
    const kebab = screen.getByTestId("entity-info-card-kebab-doc-1");
    expect(kebab).toHaveAttribute("aria-label", "Acciones");
  });

  it("kebab ⋮ click does NOT fire the card onClick (stopPropagation)", () => {
    const onClick = vi.fn();
    const actions: EntityCardAction[] = [
      { id: "edit", label: "Editar", onSelect: vi.fn() },
    ];
    renderCard({ onClick, actions });

    const kebab = screen.getByTestId("entity-info-card-kebab-doc-1");
    // Click the kebab — stopPropagation must prevent the card's onClick from firing.
    fireEvent.click(kebab);
    expect(onClick).not.toHaveBeenCalled();

    // Sanity: the card itself is still clickable (propagation only stopped from the kebab).
    fireEvent.click(screen.getByTestId("entity-info-card-doc-1"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("applies the agent-color accent (top border) via accentClass", () => {
    renderCard({ accentClass: "border-t-agent-lisa" });
    const card = screen.getByTestId("entity-info-card-doc-1");
    expect(card.className).toContain("border-t-4");
    expect(card.className).toContain("border-t-agent-lisa");
  });

  it("applies the accent via accentVar inline style when no class is given", () => {
    renderCard({ accentClass: undefined, accentVar: "--agent-lisa" });
    const card = screen.getByTestId("entity-info-card-doc-1");
    expect(card.style.borderTopColor).toBe("hsl(var(--agent-lisa))");
  });

  it("renders the metrics row (values + labels)", () => {
    renderCard();
    const metricsEl = screen.getByTestId("entity-info-card-metrics-doc-1");
    expect(metricsEl).toBeInTheDocument();
    expect(metricsEl).toHaveTextContent("8a");
    expect(metricsEl).toHaveTextContent("124");
    expect(metricsEl).toHaveTextContent("92");
    expect(metricsEl).toHaveTextContent("Pacientes");
    expect(metricsEl).toHaveTextContent("NPS");
  });

  it("renders the footer status chip", () => {
    renderCard();
    expect(screen.getByTestId("entity-info-card-status-doc-1")).toHaveTextContent("Activo");
  });
});

describe("EntityInfoCardSkeleton", () => {
  it("renders the loading placeholder", () => {
    render(<EntityInfoCardSkeleton />);
    expect(screen.getByTestId("entity-info-card-skeleton")).toBeInTheDocument();
  });
});

describe("EntityInfoCardEmpty", () => {
  it("renders the default empty state (Spanish neutro)", () => {
    render(<EntityInfoCardEmpty />);
    const empty = screen.getByTestId("entity-info-card-empty");
    expect(empty).toBeInTheDocument();
    expect(empty).toHaveTextContent("Sin elementos aún");
  });

  it("renders a custom title + action slot", () => {
    render(
      <EntityInfoCardEmpty
        title="No hay doctores"
        action={<button type="button">Agregar</button>}
      />,
    );
    expect(screen.getByTestId("entity-info-card-empty")).toHaveTextContent("No hay doctores");
    expect(screen.getByRole("button", { name: "Agregar" })).toBeInTheDocument();
  });
});
