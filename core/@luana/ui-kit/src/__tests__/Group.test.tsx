// canon: design-system-canon.md §2.6 · story-origin: core-ds-foundation
/**
 * Group.test.tsx — Vitest component tests para <Group> + <GroupHeader> + <WhatForChip>.
 *
 * Cubre:
 *  - GroupHeader renderiza título + chip "para qué".
 *  - missingFields → alert inline con role="alert" + "Falta: a, b".
 *  - sin missingFields → no hay alert.
 *  - Group hasError → borde rojo (border-destructive) + data-state=error.
 *  - Group sin error → data-state=default + border-border.
 *  - barrita de agente por accentClass (utility) y por accentVar (inline style),
 *    siempre token-driven (sin hex).
 *  - sin accent → sin border-l-4.
 *
 * core-ds-foundation T-7
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Group, GroupHeader, WhatForChip } from "../Group";

describe("WhatForChip", () => {
  it("renders the label", () => {
    render(<WhatForChip label="Para Adrián" />);
    expect(screen.getByTestId("whatfor-chip")).toHaveTextContent("Para Adrián");
  });
});

describe("GroupHeader", () => {
  it("renders title and the para-qué chip", () => {
    render(<GroupHeader title="Identidad" whatFor="Para Lisa" />);
    expect(screen.getByRole("heading", { name: "Identidad" })).toBeInTheDocument();
    expect(screen.getByTestId("whatfor-chip")).toHaveTextContent("Para Lisa");
  });

  it("shows missing fields inline with role=alert", () => {
    render(
      <GroupHeader title="Datos" missingFields={["Nombre", "Teléfono"]} />,
    );
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Falta: Nombre, Teléfono");
  });

  it("honors a custom missingLabel", () => {
    render(
      <GroupHeader title="Datos" missingFields={["X"]} missingLabel="Completa" />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Completa: X");
  });

  it("renders no alert when there are no missing fields", () => {
    render(<GroupHeader title="Datos" missingFields={[]} />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("Group — semantic error state", () => {
  it("paints a red border + data-state=error when hasError", () => {
    render(<Group hasError>contenido</Group>);
    const group = screen.getByTestId("group");
    expect(group.getAttribute("data-state")).toBe("error");
    expect(group.className).toContain("border-destructive/50");
  });

  it("uses the default border + data-state=default when no error", () => {
    render(<Group>contenido</Group>);
    const group = screen.getByTestId("group");
    expect(group.getAttribute("data-state")).toBe("default");
    expect(group.className).toContain("border-border/60");
    expect(group.className).not.toContain("border-destructive");
  });
});

describe("Group — agent-color LEFT strip (token-driven)", () => {
  it("applies accentClass utility + structural border-l-4 (no hex)", () => {
    render(<Group accentClass="border-l-agent-lisa">x</Group>);
    const group = screen.getByTestId("group");
    expect(group.className).toContain("border-l-4");
    expect(group.className).toContain("border-l-agent-lisa");
    // never an inline hex / inline borderLeftColor when only accentClass is used
    expect(group.getAttribute("style")).toBeNull();
  });

  it("applies accentVar via inline hsl(var()) style + structural border-l-4", () => {
    render(<Group accentVar="--agent-lisa">x</Group>);
    const group = screen.getByTestId("group");
    expect(group.className).toContain("border-l-4");
    expect(group.style.borderLeftColor).toBe("hsl(var(--agent-lisa))");
  });

  it("renders no left strip when no accent provided", () => {
    render(<Group>x</Group>);
    const group = screen.getByTestId("group");
    expect(group.className).not.toContain("border-l-4");
    expect(group.getAttribute("style")).toBeNull();
  });
});
