// cap: crm.adrian-embudo
// story-origin: vitalia-shell-core-hardening
/**
 * EmbudoMetrics.test.tsx — Unit + source tests for the KPI strip.
 *
 * vitalia-shell-core-hardening T-4 (Decisión A — soft-nav confiable):
 *   AC-13 — el chip 'frozen-kpi-badge' debe navegar con next/link (soft-nav),
 *   NO con un <a href> literal (band-aid B1 revertido). El edge-redirect 307 del
 *   proxy + el route real /adrian/recuperar (sin redirect in-render) eliminan el
 *   trigger del "Rendered more hooks", así que el soft-nav del chip es seguro.
 *
 * gherkin_coverage: SC-21 (mecanismo soft-nav del chip; el loop ×15 e2e vive en T-7)
 *
 * RED-first per tdd-mandatory.md: estos tests fallan mientras el chip use <a href>.
 *
 * Source test rationale: con next/link mockeado a <a>, el DOM no distingue
 * band-aid de Link. La aserción AC-13 (next/link, NO <a literal) se verifica a
 * nivel SOURCE (import Link + ausencia de <a literal), que es exactamente la
 * regresión que el band-aid introdujo.
 *
 * downstream-regression-na: brand-local vitalia embudo test; no cross-brand consumers
 * spec_anchor: 03-arch.md § Architecture Decisions A · checks "arch: frozen-kpi-badge usa next/link"
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EmbudoMetrics } from "../EmbudoMetrics";
import type { BoardKpis } from "../../../types/embudo.types";

// next/link mock → <a href> passthrough (preserva data-testid + aria-label)
vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...props
  }: {
    href: string;
    children: React.ReactNode;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

const TENANT = "e69a691d-070e-5caf-a053-6e74642ec100";

const KPIS: BoardKpis = {
  totalActive: 42,
  adrianCount: 30,
  humanCount: 12,
  hotCount: 8,
  warmCount: 6,
  coldCount: 5,
  avgScore: 71,
  depositRate: 0.27,
  frozenCount: 3,
};

const SOURCE = readFileSync(
  path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "../EmbudoMetrics.tsx",
  ),
  "utf8",
);

describe("EmbudoMetrics — render (SC-21 mecanismo soft-nav)", () => {
  it("renderiza la tira con todos los chips KPI", () => {
    render(<EmbudoMetrics kpis={KPIS} tenantId={TENANT} />);
    expect(screen.getByTestId("embudo-metrics")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("27%")).toBeInTheDocument();
  });

  it("el chip 'congelados' (frozen-kpi-badge) linkea a /{tenant}/adrian/recuperar", () => {
    render(<EmbudoMetrics kpis={KPIS} tenantId={TENANT} />);
    const chip = screen.getByTestId("frozen-kpi-badge");
    expect(chip).toHaveAttribute("href", `/${TENANT}/adrian/recuperar`);
  });

  it("el chip frozen tiene aria-label accesible (recuperar)", () => {
    render(<EmbudoMetrics kpis={KPIS} tenantId={TENANT} />);
    expect(screen.getByTestId("frozen-kpi-badge")).toHaveAttribute(
      "aria-label",
      expect.stringContaining("Recuperar"),
    );
  });
});

describe("EmbudoMetrics — AC-13: soft-nav vía next/link (band-aid B1 revertido)", () => {
  it("importa Link de next/link (soft-nav)", () => {
    expect(SOURCE).toMatch(/import\s+Link\s+from\s+["']next\/link["']/);
  });

  it("NO usa un <a href> literal para el chip (band-aid hard-nav eliminado)", () => {
    // El band-aid usaba `<a key=... href={chip.href} ...>`. El revert debe
    // dejar el navegable como <Link>, sin ninguna etiqueta <a> JSX manual.
    // Regex acotada al tag JSX (`<a ` o `<a>`) — no matchea prose en comentarios.
    expect(SOURCE).not.toMatch(/<a[\s>]/);
  });

  it("usa <Link href={...}> para el navegable del chip", () => {
    expect(SOURCE).toMatch(/<Link\b[\s\S]*?href=/);
  });
});
