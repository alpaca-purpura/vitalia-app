// canon: design-system-canon.md §2.6 · story-origin: core-ds-foundation
/**
 * FloatingAutosaveIndicator.test.tsx — Vitest component tests.
 *
 * Cubre:
 *  - Renderiza con role="status" (announceable).
 *  - data-state refleja el status.
 *  - label correcto por estado (saving / saved / error / idle / dirty).
 *  - "Guardado" + tiempo relativo cuando hay savedAt.
 *  - wrapper pointer-events-none + píldora pointer-events-auto (no bloquea contenido).
 *  - aria-live assertive solo en error.
 *  - UNA sola instancia por render (SSoT canon §2.6) — un único role=status.
 *  - override de labels (i18n).
 *
 * core-ds-foundation T-7
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { AutosaveStatus } from "@luana/hooks";
import { FloatingAutosaveIndicator } from "../FloatingAutosaveIndicator";

describe("FloatingAutosaveIndicator — role + data-state", () => {
  it("renders a single status region (one per page)", () => {
    render(<FloatingAutosaveIndicator status="idle" />);
    expect(screen.getAllByRole("status")).toHaveLength(1);
  });

  const statuses: AutosaveStatus[] = ["idle", "dirty", "saving", "saved", "error"];
  for (const status of statuses) {
    it(`reflects data-state="${status}"`, () => {
      render(<FloatingAutosaveIndicator status={status} />);
      const pill = screen.getByTestId("autosave-indicator");
      expect(pill.getAttribute("data-state")).toBe(status);
    });
  }
});

describe("FloatingAutosaveIndicator — labels", () => {
  it("shows the saving label", () => {
    render(<FloatingAutosaveIndicator status="saving" />);
    expect(screen.getByText("Guardando…")).toBeInTheDocument();
  });

  it("shows the saved label without savedAt", () => {
    render(<FloatingAutosaveIndicator status="saved" />);
    expect(screen.getByText("Guardado")).toBeInTheDocument();
  });

  it("appends relative time when status=saved + savedAt", () => {
    render(<FloatingAutosaveIndicator status="saved" savedAt={new Date()} />);
    expect(screen.getByText(/Guardado ahora mismo/)).toBeInTheDocument();
  });

  it("shows the error label", () => {
    render(<FloatingAutosaveIndicator status="error" />);
    expect(
      screen.getByText("Error al guardar. Vuelve a intentarlo."),
    ).toBeInTheDocument();
  });

  it("shows the idle helper label (always visible)", () => {
    render(<FloatingAutosaveIndicator status="idle" />);
    expect(
      screen.getByText("Los cambios se guardan automáticamente"),
    ).toBeInTheDocument();
  });

  it("honors a custom label override (i18n)", () => {
    render(
      <FloatingAutosaveIndicator
        status="saved"
        labels={{ saved: "Saved" }}
      />,
    );
    expect(screen.getByText("Saved")).toBeInTheDocument();
  });
});

describe("FloatingAutosaveIndicator — accessibility & layering", () => {
  it("error uses aria-live=assertive; others polite", () => {
    const { rerender } = render(<FloatingAutosaveIndicator status="error" />);
    expect(screen.getByRole("status").getAttribute("aria-live")).toBe(
      "assertive",
    );
    rerender(<FloatingAutosaveIndicator status="saving" />);
    expect(screen.getByRole("status").getAttribute("aria-live")).toBe("polite");
  });

  it("wrapper is pointer-events-none; pill is pointer-events-auto", () => {
    const { container } = render(<FloatingAutosaveIndicator status="idle" />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain("pointer-events-none");
    const pill = screen.getByTestId("autosave-indicator");
    expect(pill.className).toContain("pointer-events-auto");
  });

  it('anchor defaults to "sheet" → absolute to the hoja frame, not the viewport', () => {
    const { container } = render(<FloatingAutosaveIndicator status="idle" />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain("absolute");
    expect(wrapper.className).toContain("bottom-4");
    expect(wrapper.className).not.toContain("fixed");
  });

  it('anchor="page" → fixed to the viewport (escape hatch)', () => {
    const { container } = render(<FloatingAutosaveIndicator status="idle" anchor="page" />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain("fixed");
    expect(wrapper.className).not.toContain("absolute");
  });
});
