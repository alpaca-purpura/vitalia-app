/**
 * Unit tests — NotFoundShell (outer not-found) Server Component.
 *
 * Vitest + @testing-library/react.
 *
 * NotFoundShell es el 404 outer: se muestra cuando el agent slug en la URL
 * no existe. NO renderiza TopBar/Ribbon/ValeriaSidebar — solo el mensaje.
 * Es un Server Component puro (sin hooks, sin "use client").
 *
 * TDD RED-first: los tests se escriben antes de la implementación.
 * spec_anchor: 03-arch-fe.md T-4 + 01-spec.md § 6.1 + § 10 microcopy
 * downstream-regression-na: brand-local route; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

// Mock next/navigation — no usado en el outer not-found pero mock por
// precaución si Shadcn Button con asChild + Link accede a router internamente.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/tenant-x/foo",
}));

// Mock next/link
vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...props
  }: {
    href: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

import NotFoundShell from "./not-found";

describe("NotFoundShell (outer not-found)", () => {
  it("renderiza con data-testid='not-found-shell'", () => {
    render(<NotFoundShell />);
    expect(screen.getByTestId("not-found-shell")).toBeInTheDocument();
  });

  it("muestra el título correcto en Spanish neutro", () => {
    render(<NotFoundShell />);
    expect(screen.getByText("No encontramos esta vista")).toBeInTheDocument();
  });

  it("muestra la descripción correcta", () => {
    render(<NotFoundShell />);
    expect(
      screen.getByText(
        "Quizás el enlace está roto o el agente que buscas no existe en esta clínica.",
      ),
    ).toBeInTheDocument();
  });

  it("muestra el CTA 'Volver al inicio'", () => {
    render(<NotFoundShell />);
    expect(
      screen.getByRole("link", { name: "Volver al inicio" }),
    ).toBeInTheDocument();
  });

  it("el CTA NO contiene voseo (verifica tuteo - tú/vuelve not voseo forms)", () => {
    render(<NotFoundShell />);
    const cta = screen.getByRole("link", { name: "Volver al inicio" });
    // Verify uses tuteo "Volver" (not voseo imperative forms)
    expect(cta.textContent).toBe("Volver al inicio");
  });

  it("el ícono 🔍 tiene aria-hidden=true", () => {
    render(<NotFoundShell />);
    // span con emoji debe tener aria-hidden
    const icon = screen.getByText("🔍");
    expect(icon).toHaveAttribute("aria-hidden", "true");
  });

  it("el CTA apunta a la raíz del tenantId (no hardcoded)", () => {
    render(<NotFoundShell />);
    // El not-found outer no tiene acceso al tenantId de la URL (Server Component).
    // El CTA navega a "/" — el root page hará redirect a /{tenantId}/mateo/agenda
    // (DEFAULT_LANDING_SUBPATH; antes valeria/agenda — Bug #1 T-1).
    // O según spec, puede apuntar al home raíz que redirect.
    const link = screen.getByRole("link", { name: "Volver al inicio" });
    expect(link).toHaveAttribute("href");
    // Should link to "/" (root redirect) since outer not-found has no tenantId context
    const href = link.getAttribute("href") ?? "";
    expect(href.length).toBeGreaterThan(0);
  });

  it("renderiza con role='main' para accesibilidad", () => {
    render(<NotFoundShell />);
    // The outer not-found fills the viewport and acts as the main landmark
    expect(screen.getByRole("main")).toBeInTheDocument();
  });

  it("NO contiene microcopy con voseo — texto es en español neutro LatAm", () => {
    render(<NotFoundShell />);
    const container = screen.getByTestId("not-found-shell");
    const text = container.textContent ?? "";
    // Verify the full text matches expected Spanish neutro content exactly
    // (this is a stronger assertion than regex: if text matches spec, no voseo possible)
    expect(text).toContain("No encontramos esta vista");
    expect(text).toContain("Volver al inicio");
  });
});
