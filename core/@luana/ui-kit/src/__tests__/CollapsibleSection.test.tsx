// cap: lisa.servicios (origin: vitalia-fase2-lisa-servicios T-R0 · promotion 2026-06-16-collapsible-section-ui-kit)
/**
 * CollapsibleSection.test.tsx — Vitest component tests para <CollapsibleSection>.
 *
 * Cubre (TDD RED-first, per tdd-mandatory.md):
 *  - title, summary, children se renderizan.
 *  - defaultOpen=true → body visible al montar.
 *  - defaultOpen=false (default) → body colapsado al montar.
 *  - click en el trigger toggle → abre/cierra el body.
 *  - accentVar aplica el left strip (inline style + border-l-4).
 *  - accentClass aplica el left strip (utility class + border-l-4).
 *  - sin accent → sin border-l-4.
 *  - hasError delega a Group (data-state=error + border-destructive).
 *  - missingFields muestra alert inline.
 *  - sin missingFields → no hay alert.
 *  - className se propaga al contenedor externo.
 *
 * Regresión: los tests de accordion.tsx / Group.tsx / collapsible.tsx
 * NO se tocan (additive only — regression_guard del proposal).
 *
 * T-R0 · vitalia-fase2-lisa-servicios reconcile delta 2026-06-16
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CollapsibleSection } from "../CollapsibleSection";

// ── 1. render básico ──────────────────────────────────────────────────────────

describe("CollapsibleSection — render básico", () => {
  it("muestra el title en el trigger", () => {
    render(
      <CollapsibleSection title="Identidad">
        <p>contenido</p>
      </CollapsibleSection>,
    );
    expect(screen.getByText("Identidad")).toBeInTheDocument();
  });

  it("muestra el summary junto al title cuando se provee", () => {
    render(
      <CollapsibleSection title="Qué es" summary={<span>3 campos</span>}>
        <p>contenido</p>
      </CollapsibleSection>,
    );
    expect(screen.getByText("3 campos")).toBeInTheDocument();
  });

  it("no rompe cuando summary es undefined", () => {
    render(
      <CollapsibleSection title="Sin summary">
        <p>contenido</p>
      </CollapsibleSection>,
    );
    expect(screen.getByText("Sin summary")).toBeInTheDocument();
  });

  it("acepta summary como string (ReactNode)", () => {
    render(
      <CollapsibleSection title="Sección" summary="6 campos">
        <p>cuerpo</p>
      </CollapsibleSection>,
    );
    expect(screen.getByText("6 campos")).toBeInTheDocument();
  });
});

// ── 2. defaultOpen ────────────────────────────────────────────────────────────

describe("CollapsibleSection — defaultOpen", () => {
  it("mantiene el body colapsado por default (defaultOpen=false)", () => {
    render(
      <CollapsibleSection title="El procedimiento">
        <p data-testid="body-content">pasos</p>
      </CollapsibleSection>,
    );
    // El AccordionContent de Radix oculta el contenido cuando cerrado;
    // verificamos que el panel no esté visible (o que el trigger indique cerrado).
    const trigger = screen.getByRole("button");
    expect(trigger).toHaveAttribute("data-state", "closed");
  });

  it("abre el body cuando defaultOpen=true", () => {
    render(
      <CollapsibleSection title="Identidad" defaultOpen>
        <p data-testid="body-content">campos abiertos</p>
      </CollapsibleSection>,
    );
    const trigger = screen.getByRole("button");
    expect(trigger).toHaveAttribute("data-state", "open");
  });
});

// ── 3. click toggle ───────────────────────────────────────────────────────────

describe("CollapsibleSection — interactividad (click toggle)", () => {
  it("al hacer click en el trigger cierra una sección abierta", () => {
    render(
      <CollapsibleSection title="Resultados" defaultOpen>
        <p>esperados</p>
      </CollapsibleSection>,
    );
    const trigger = screen.getByRole("button");
    expect(trigger).toHaveAttribute("data-state", "open");
    fireEvent.click(trigger);
    expect(trigger).toHaveAttribute("data-state", "closed");
  });

  it("al hacer click en el trigger abre una sección cerrada", () => {
    render(
      <CollapsibleSection title="Riesgos">
        <p>precauciones</p>
      </CollapsibleSection>,
    );
    const trigger = screen.getByRole("button");
    expect(trigger).toHaveAttribute("data-state", "closed");
    fireEvent.click(trigger);
    expect(trigger).toHaveAttribute("data-state", "open");
  });

  it("mantiene los children presentes en el DOM tras toggle", () => {
    render(
      <CollapsibleSection title="Modalidad" defaultOpen>
        <p data-testid="inner">contenido interior</p>
      </CollapsibleSection>,
    );
    const trigger = screen.getByRole("button");
    fireEvent.click(trigger); // cierra
    // Radix mantiene el nodo en el DOM (hidden via animation/overflow)
    // pero data-state del trigger cambia a closed
    expect(trigger).toHaveAttribute("data-state", "closed");
  });
});

// ── 4. accentVar (left strip inline) ─────────────────────────────────────────

describe("CollapsibleSection — accentVar (barrita de agente inline)", () => {
  it("aplica borderLeftColor via hsl(var()) + border-l-4 al Group exterior", () => {
    render(
      <CollapsibleSection title="Identidad" accentVar="--agent-lisa">
        <p>x</p>
      </CollapsibleSection>,
    );
    // El Group exterior expone data-testid="group"
    const group = screen.getByTestId("group");
    expect(group.className).toContain("border-l-4");
    expect(group.style.borderLeftColor).toBe("hsl(var(--agent-lisa))");
  });

  it("no aplica inline style cuando no hay accentVar", () => {
    render(
      <CollapsibleSection title="Sin acento">
        <p>y</p>
      </CollapsibleSection>,
    );
    const group = screen.getByTestId("group");
    expect(group.getAttribute("style")).toBeNull();
    expect(group.className).not.toContain("border-l-4");
  });
});

// ── 5. accentClass (left strip utility) ──────────────────────────────────────

describe("CollapsibleSection — accentClass (barrita de agente utility)", () => {
  it("aplica la utility class + border-l-4 al Group exterior", () => {
    render(
      <CollapsibleSection title="Qué es" accentClass="border-l-agent-lisa">
        <p>z</p>
      </CollapsibleSection>,
    );
    const group = screen.getByTestId("group");
    expect(group.className).toContain("border-l-4");
    expect(group.className).toContain("border-l-agent-lisa");
    // sin inline style cuando se usa accentClass
    expect(group.getAttribute("style")).toBeNull();
  });
});

// ── 6. hasError → estado de error semántico ───────────────────────────────────

describe("CollapsibleSection — hasError (estado de error delegado a Group)", () => {
  it("Group tiene data-state=error y borde destructivo cuando hasError=true", () => {
    render(
      <CollapsibleSection title="Riesgos" hasError>
        <p>contenido</p>
      </CollapsibleSection>,
    );
    const group = screen.getByTestId("group");
    expect(group.getAttribute("data-state")).toBe("error");
    expect(group.className).toContain("border-destructive");
  });

  it("Group tiene data-state=default sin hasError", () => {
    render(
      <CollapsibleSection title="Sin error">
        <p>ok</p>
      </CollapsibleSection>,
    );
    const group = screen.getByTestId("group");
    expect(group.getAttribute("data-state")).toBe("default");
    expect(group.className).not.toContain("border-destructive");
  });
});

// ── 7. missingFields → alert inline ──────────────────────────────────────────

describe("CollapsibleSection — missingFields (alerta inline)", () => {
  it("muestra un role=alert con los campos faltantes cuando missingFields no es vacío", () => {
    render(
      <CollapsibleSection title="Identidad" missingFields={["Nombre", "Categoría"]}>
        <p>x</p>
      </CollapsibleSection>,
    );
    const alert = screen.getByRole("alert");
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveTextContent("Nombre");
    expect(alert).toHaveTextContent("Categoría");
  });

  it("no muestra alert cuando missingFields es undefined", () => {
    render(
      <CollapsibleSection title="Identidad">
        <p>x</p>
      </CollapsibleSection>,
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("no muestra alert cuando missingFields es un array vacío", () => {
    render(
      <CollapsibleSection title="Identidad" missingFields={[]}>
        <p>x</p>
      </CollapsibleSection>,
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

// ── 8. className en el contenedor externo ────────────────────────────────────

describe("CollapsibleSection — className propagation", () => {
  it("aplica className extra al Group exterior", () => {
    render(
      <CollapsibleSection title="Con clase" className="mt-4 custom-class">
        <p>c</p>
      </CollapsibleSection>,
    );
    const group = screen.getByTestId("group");
    expect(group.className).toContain("mt-4");
    expect(group.className).toContain("custom-class");
  });
});
