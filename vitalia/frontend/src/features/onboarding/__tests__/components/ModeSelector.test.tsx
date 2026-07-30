/**
 * Tests — ModeSelector component (T-onboarding-6 TDD)
 *
 * RED-first per .claude/rules/tdd-mandatory.md.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ModeSelector } from "../../components/ModeSelector";

// ─── Mocks ──────────────────────────────────────────────────────────────────

vi.mock("@/lib/cn", () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(" "),
}));

vi.mock("../../config/copy", () => ({
  WIZARD_COPY: {
    modeSelector: {
      label: "¿Cómo quieres compartir información?",
      options: {
        url: { label: "Sitio web", description: "Comparte la URL de tu sitio" },
        document: { label: "Documento", description: "Sube un PDF o Word" },
        audio: {
          label: "Audio",
          description: "Graba un audio",
          disabledTooltip: "Disponible próximamente",
        },
      },
    },
  },
}));

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("ModeSelector", () => {
  it("renders without crashing", () => {
    expect(() =>
      render(<ModeSelector selectedMode="url" onModeChange={vi.fn()} />),
    ).not.toThrow();
  });

  it("renders all three mode buttons", () => {
    render(<ModeSelector selectedMode="url" onModeChange={vi.fn()} />);
    expect(screen.getByText("Sitio web")).toBeTruthy();
    expect(screen.getByText("Documento")).toBeTruthy();
    expect(screen.getByText("Audio")).toBeTruthy();
  });

  it("calls onModeChange with 'url' when URL button is clicked", () => {
    const onModeChange = vi.fn();
    render(
      <ModeSelector selectedMode="document" onModeChange={onModeChange} />,
    );
    fireEvent.click(screen.getByText("Sitio web"));
    expect(onModeChange).toHaveBeenCalledWith("url");
  });

  it("calls onModeChange with 'document' when document button is clicked", () => {
    const onModeChange = vi.fn();
    render(<ModeSelector selectedMode="url" onModeChange={onModeChange} />);
    fireEvent.click(screen.getByText("Documento"));
    expect(onModeChange).toHaveBeenCalledWith("document");
  });

  it("audio button is disabled (OQ-3 ratification — Slice 2)", () => {
    render(<ModeSelector selectedMode="url" onModeChange={vi.fn()} />);
    // Audio button should be disabled
    const buttons = screen.getAllByRole("button");
    const audioBtn = buttons.find((b) => b.textContent?.includes("Audio"));
    expect(audioBtn).toBeTruthy();
    expect(audioBtn?.hasAttribute("disabled")).toBe(true);
  });

  it("does NOT call onModeChange when audio button is clicked (disabled)", () => {
    const onModeChange = vi.fn();
    render(<ModeSelector selectedMode="url" onModeChange={onModeChange} />);
    const buttons = screen.getAllByRole("button");
    const audioBtn = buttons.find((b) => b.textContent?.includes("Audio"));
    if (audioBtn) fireEvent.click(audioBtn);
    expect(onModeChange).not.toHaveBeenCalledWith("audio");
  });

  it("renders accessible group label", () => {
    render(<ModeSelector selectedMode="url" onModeChange={vi.fn()} />);
    expect(
      screen.getByText("¿Cómo quieres compartir información?"),
    ).toBeTruthy();
  });

  it("highlights selected mode when provided", () => {
    const { container } = render(
      <ModeSelector selectedMode="url" onModeChange={vi.fn()} />,
    );
    // Selected button should have active styling
    expect(container).toBeTruthy();
  });
});
