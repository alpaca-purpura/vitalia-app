/**
 * NPSTagBadge — Unit tests (TDD RED-first per .claude/rules/tdd-mandatory.md)
 *
 * Tests cover:
 *   1. Score 5 → detractor category + rojo visual class
 *   2. Score 7 → pasivo category + amarillo visual class
 *   3. Score 10 → promotor category + verde visual class
 *   4. aria-label correcto per spec (§NPSTagBadge in 03-arch-fe.md)
 *   5. Size variants apply correct classes (sm / md / lg)
 *   6. Variant prop (badge / chip / tag)
 *   7. Null/undefined score renders gracefully (sin NPS)
 *   8. Score boundaries (0 → detractor, 6 → detractor, 7 → pasivo, 8 → pasivo, 9 → promotor)
 *
 * downstream-regression-na: vitalia-local shared component — no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { NPSTagBadge } from "../NPSTagBadge";

describe("NPSTagBadge", () => {
  // ──────────────────────────────────────────────────────────────────
  // Category detection
  // ──────────────────────────────────────────────────────────────────

  it("score 5 → detractor → tiene clase vt-bg-danger-12", () => {
    render(<NPSTagBadge score={5} />);
    const badge = screen.getByRole("status");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("vt-bg-danger-12");
    expect(badge.className).toContain("vt-text-danger");
  });

  it("score 7 → pasivo → tiene clase vt-bg-warning-12", () => {
    render(<NPSTagBadge score={7} />);
    const badge = screen.getByRole("status");
    expect(badge.className).toContain("vt-bg-warning-12");
    expect(badge.className).toContain("vt-text-warning");
  });

  it("score 10 → promotor → tiene clase vt-bg-success-12", () => {
    render(<NPSTagBadge score={10} />);
    const badge = screen.getByRole("status");
    expect(badge.className).toContain("vt-bg-success-12");
    expect(badge.className).toContain("vt-text-success");
  });

  // ──────────────────────────────────────────────────────────────────
  // aria-label (WCAG AA — spec: "Calificación NPS {score}, categoría {cat}")
  // ──────────────────────────────────────────────────────────────────

  it("aria-label score 5 → 'Calificación NPS 5, categoría detractor'", () => {
    render(<NPSTagBadge score={5} />);
    expect(screen.getByRole("status")).toHaveAttribute(
      "aria-label",
      "Calificación NPS 5, categoría detractor",
    );
  });

  it("aria-label score 7 → 'Calificación NPS 7, categoría pasivo'", () => {
    render(<NPSTagBadge score={7} />);
    expect(screen.getByRole("status")).toHaveAttribute(
      "aria-label",
      "Calificación NPS 7, categoría pasivo",
    );
  });

  it("aria-label score 10 → 'Calificación NPS 10, categoría promotor'", () => {
    render(<NPSTagBadge score={10} />);
    expect(screen.getByRole("status")).toHaveAttribute(
      "aria-label",
      "Calificación NPS 10, categoría promotor",
    );
  });

  // ──────────────────────────────────────────────────────────────────
  // Label text visible
  // ──────────────────────────────────────────────────────────────────

  it("score 5 muestra 'NPS 5' en el texto visible", () => {
    render(<NPSTagBadge score={5} />);
    expect(screen.getByText(/NPS 5/)).toBeInTheDocument();
  });

  // ──────────────────────────────────────────────────────────────────
  // Score boundaries
  // ──────────────────────────────────────────────────────────────────

  it("score 0 → detractor", () => {
    render(<NPSTagBadge score={0} />);
    expect(screen.getByRole("status").dataset.npsCategory).toBe("detractor");
  });

  it("score 6 → detractor", () => {
    render(<NPSTagBadge score={6} />);
    expect(screen.getByRole("status").dataset.npsCategory).toBe("detractor");
  });

  it("score 8 → pasivo", () => {
    render(<NPSTagBadge score={8} />);
    expect(screen.getByRole("status").dataset.npsCategory).toBe("passive");
  });

  it("score 9 → promotor", () => {
    render(<NPSTagBadge score={9} />);
    expect(screen.getByRole("status").dataset.npsCategory).toBe("promoter");
  });

  // ──────────────────────────────────────────────────────────────────
  // Null / undefined — graceful fallback
  // ──────────────────────────────────────────────────────────────────

  it("score null → renders 'Sin NPS' fallback accesible", () => {
    render(<NPSTagBadge score={null} />);
    expect(screen.getByText("Sin NPS")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveAttribute(
      "aria-label",
      "NPS: sin datos",
    );
  });

  it("score undefined → renders 'Sin NPS' fallback", () => {
    render(<NPSTagBadge score={undefined} />);
    expect(screen.getByText("Sin NPS")).toBeInTheDocument();
  });

  // ──────────────────────────────────────────────────────────────────
  // Size variants
  // ──────────────────────────────────────────────────────────────────

  it("size='sm' aplica clase de texto xs", () => {
    render(<NPSTagBadge score={8} size="sm" />);
    const badge = screen.getByRole("status");
    expect(badge.className).toContain("text-xs");
  });

  it("size='md' aplica clase de texto sm (default)", () => {
    render(<NPSTagBadge score={8} size="md" />);
    const badge = screen.getByRole("status");
    expect(badge.className).toContain("text-sm");
  });

  it("size='lg' aplica clase de texto base", () => {
    render(<NPSTagBadge score={8} size="lg" />);
    const badge = screen.getByRole("status");
    expect(badge.className).toContain("text-base");
  });

  // ──────────────────────────────────────────────────────────────────
  // Variant prop
  // ──────────────────────────────────────────────────────────────────

  it("variant='chip' aplica border radius pill", () => {
    render(<NPSTagBadge score={9} variant="chip" />);
    const badge = screen.getByRole("status");
    expect(badge.className).toContain("rounded-[var(--radius-pill)]");
  });

  it("variant='badge' aplica border radius standard (default)", () => {
    render(<NPSTagBadge score={9} variant="badge" />);
    const badge = screen.getByRole("status");
    expect(badge.className).toContain("rounded-[var(--radius)]");
  });

  it("variant='tag' aplica border radius sm", () => {
    render(<NPSTagBadge score={9} variant="tag" />);
    const badge = screen.getByRole("status");
    expect(badge.className).toContain("rounded-sm");
  });

  // ──────────────────────────────────────────────────────────────────
  // className passthrough
  // ──────────────────────────────────────────────────────────────────

  it("className extra se aplica al elemento raíz", () => {
    render(<NPSTagBadge score={9} className="custom-cls" />);
    expect(screen.getByRole("status").className).toContain("custom-cls");
  });

  // ──────────────────────────────────────────────────────────────────
  // data-testid (stable key for consumers)
  // ──────────────────────────────────────────────────────────────────

  it("expone data-nps-category para testing y selectores estables", () => {
    render(<NPSTagBadge score={5} />);
    const badge = screen.getByRole("status");
    expect(badge.dataset.npsCategory).toBe("detractor");
  });
});
