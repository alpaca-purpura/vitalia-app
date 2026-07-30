/**
 * error.test.tsx — Vitest unit tests for the generic [agent] error boundary.
 *
 * Bug #7 (vitalia-bugfix-shell-nav-scroll-errors T-3):
 *   El error de una hoja se aísla al panel; el fallback muestra un mensaje +
 *   botón Reintentar que llama reset() (re-monta el sub-árbol). El fallback NO
 *   ocupa toda la pantalla (flex flex-1, vive dentro del slot de contenido) →
 *   el chrome/nav del shell queda vivo (RN-6).
 *
 * El aislamiento real (chrome vivo) se verifica en e2e (forzar throw → nav
 * clickeable). Acá probamos el contrato del boundary en aislamiento.
 *
 * downstream-regression-na: brand-local route boundary test; no cross-brand consumers
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import AgentError from "./error";

const VOSEO_TOKENS =
  /\b(vos|sos|tenés|podés|mirá|dejá|poné|usá|hacé|elegí|agregá|configurá|revisá|guardá|abrí|volvé|cambiá|seleccioná|escribí|fijate|dale)\b/i;

describe("AgentError boundary — Bug #7 (RN-6)", () => {
  it("renderiza el fallback con título + descripción (mensaje accesible)", () => {
    render(<AgentError error={new Error("boom")} reset={vi.fn()} />);
    expect(screen.getByTestId("agent-error-boundary")).toBeInTheDocument();
    expect(
      screen.getByText("No se pudo cargar esta sección"),
    ).toBeInTheDocument();
  });

  it("el fallback es role='alert' aria-live='assertive' (a11y)", () => {
    render(<AgentError error={new Error("boom")} reset={vi.fn()} />);
    const alert = screen.getByTestId("agent-error-boundary");
    expect(alert.getAttribute("role")).toBe("alert");
    expect(alert.getAttribute("aria-live")).toBe("assertive");
  });

  it("el botón Reintentar llama reset() (re-monta el sub-árbol)", () => {
    const reset = vi.fn();
    render(<AgentError error={new Error("boom")} reset={reset} />);
    const retry = screen.getByTestId("agent-error-retry");
    expect(retry).toBeInTheDocument();
    fireEvent.click(retry);
    expect(reset).toHaveBeenCalledTimes(1);
  });

  it("el fallback ocupa el panel (flex flex-1) — NO toda la pantalla (no h-screen)", () => {
    render(<AgentError error={new Error("boom")} reset={vi.fn()} />);
    const root = screen.getByTestId("agent-error-boundary");
    expect(root.className).toContain("flex-1");
    expect(root.className).not.toContain("h-screen");
    expect(root.className).not.toContain("fixed");
  });

  it("microcopy en español neutro LatAm (sin voseo)", () => {
    render(<AgentError error={new Error("boom")} reset={vi.fn()} />);
    const text = document.body.textContent ?? "";
    expect(text).not.toMatch(VOSEO_TOKENS);
    // "Reintentar" + "Puedes intentar" (tuteo) presentes
    expect(text).toContain("Reintentar");
    expect(text).toContain("Puedes");
  });

  it("es default export (requisito Next.js error.tsx)", () => {
    expect(typeof AgentError).toBe("function");
  });
});
