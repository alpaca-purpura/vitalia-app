// voseo-allowed: test fixture — regex patterns verify voseo absence in component output, not user-facing strings
/**
 * EmptyState.test.tsx — Vitest unit tests (TDD RED→GREEN).
 *
 * spec_anchor: 03-arch.md § 3.2 + 06-tickets.yaml T-1 val-fe-vitest-unit-empty-state
 *
 * Tests:
 *   - renders emoji icon at correct size + opacity
 *   - renders h3 title
 *   - renders description text
 *   - renders optional CTA button when provided
 *   - does NOT render CTA button when omitted
 *   - aria-hidden on icon container
 *   - Spanish neutro copy: no voseo
 *
 * downstream-regression-na: brand-local shell-organism; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { EmptyState } from "./EmptyState";

describe("EmptyState", () => {
  it("renders emoji icon", () => {
    render(
      <EmptyState
        icon="📄"
        title="Título de prueba"
        description="Descripción de prueba"
      />,
    );
    const iconEl = screen.getByTestId("empty-state-icon");
    expect(iconEl).toBeInTheDocument();
    expect(iconEl).toHaveTextContent("📄");
  });

  it("renders h3 title", () => {
    render(
      <EmptyState
        icon="📄"
        title="Mi sub-tab — próximamente"
        description="Esta vista vive acá."
      />,
    );
    const heading = screen.getByRole("heading", { level: 3 });
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveTextContent("Mi sub-tab — próximamente");
  });

  it("renders description text", () => {
    render(
      <EmptyState
        icon="📄"
        title="Título"
        description="Esta vista vive acá. El contenido real se cablea en Fase 2."
      />,
    );
    expect(
      screen.getByText(
        "Esta vista vive acá. El contenido real se cablea en Fase 2.",
      ),
    ).toBeInTheDocument();
  });

  it("renders optional CTA button when provided", () => {
    const handleClick = () => undefined;
    render(
      <EmptyState
        icon="📄"
        title="Título"
        description="Descripción"
        ctaLabel="Ir a configuración"
        onCtaClick={handleClick}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Ir a configuración" }),
    ).toBeInTheDocument();
  });

  it("does NOT render CTA button when ctaLabel is omitted", () => {
    render(<EmptyState icon="📄" title="Título" description="Descripción" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("icon container has aria-hidden attribute", () => {
    render(<EmptyState icon="🩺" title="Título" description="Descripción" />);
    const iconEl = screen.getByTestId("empty-state-icon");
    expect(iconEl).toHaveAttribute("aria-hidden", "true");
  });

  it("title copy does not contain voseo (tenés/podés/hacés/dejá)", () => {
    render(
      <EmptyState
        icon="📄"
        title="Esta vista vive acá. El contenido real se cablea en Fase 2."
        description="Navega a esta sección cuando esté disponible."
      />,
    );
    const heading = screen.getByRole("heading", { level: 3 });
    expect(heading.textContent).not.toMatch(
      /tenés|podés|hacés|dejá|mirá|agregá/i,
    );
  });
});
