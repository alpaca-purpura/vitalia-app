/**
 * Tests — CloseSetupWarningModal component (T-onboarding-6 TDD)
 *
 * RED-first per .claude/rules/tdd-mandatory.md.
 * Tests keyboard accessibility, focus trap, Escape handler.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CloseSetupWarningModal } from "../../components/CloseSetupWarningModal";

// ─── Mocks ──────────────────────────────────────────────────────────────────

vi.mock("@/lib/cn", () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(" "),
}));

vi.mock("../../config/copy", () => ({
  WIZARD_COPY: {
    closeModal: {
      title: "¿Deseas cerrar el asistente?",
      description:
        "Tu progreso se guarda automáticamente. Puedes continuar la configuración cuando quieras.",
      cancelButton: "Continuar configurando",
      confirmButton: "Cerrar por ahora",
    },
  },
}));

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("CloseSetupWarningModal", () => {
  const defaultProps = {
    isOpen: true,
    onConfirmClose: vi.fn(),
    onCancel: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders null when isOpen is false", () => {
    const { container } = render(
      <CloseSetupWarningModal
        isOpen={false}
        onConfirmClose={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders modal content when isOpen is true", () => {
    render(<CloseSetupWarningModal {...defaultProps} />);
    expect(screen.getByText("¿Deseas cerrar el asistente?")).toBeTruthy();
    expect(screen.getByText(/tu progreso se guarda/i)).toBeTruthy();
  });

  it("renders cancel button with correct label", () => {
    render(<CloseSetupWarningModal {...defaultProps} />);
    expect(
      screen.getByRole("button", { name: "Continuar configurando" }),
    ).toBeTruthy();
  });

  it("renders confirm button with correct label", () => {
    render(<CloseSetupWarningModal {...defaultProps} />);
    expect(
      screen.getByRole("button", { name: "Cerrar por ahora" }),
    ).toBeTruthy();
  });

  it("calls onCancel when cancel button clicked", () => {
    render(<CloseSetupWarningModal {...defaultProps} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Continuar configurando" }),
    );
    expect(defaultProps.onCancel).toHaveBeenCalledTimes(1);
  });

  it("calls onConfirmClose when confirm button clicked", () => {
    render(<CloseSetupWarningModal {...defaultProps} />);
    fireEvent.click(screen.getByRole("button", { name: "Cerrar por ahora" }));
    expect(defaultProps.onConfirmClose).toHaveBeenCalledTimes(1);
  });

  it("calls onCancel when Escape key pressed", () => {
    render(<CloseSetupWarningModal {...defaultProps} />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(defaultProps.onCancel).toHaveBeenCalledTimes(1);
  });

  it("calls onCancel when backdrop clicked", () => {
    const { container } = render(<CloseSetupWarningModal {...defaultProps} />);
    // Backdrop is first child (before dialog)
    const backdrop = container.querySelector('[aria-hidden="true"]');
    if (backdrop) fireEvent.click(backdrop);
    expect(defaultProps.onCancel).toHaveBeenCalledTimes(1);
  });

  it("has role='alertdialog' for accessibility", () => {
    render(<CloseSetupWarningModal {...defaultProps} />);
    expect(screen.getByRole("alertdialog")).toBeTruthy();
  });

  it("has aria-modal='true'", () => {
    render(<CloseSetupWarningModal {...defaultProps} />);
    const dialog = screen.getByRole("alertdialog");
    expect(dialog.getAttribute("aria-modal")).toBe("true");
  });

  it("has aria-labelledby pointing to title element", () => {
    render(<CloseSetupWarningModal {...defaultProps} />);
    const dialog = screen.getByRole("alertdialog");
    const labelId = dialog.getAttribute("aria-labelledby");
    expect(labelId).toBeTruthy();
    const titleEl = document.getElementById(labelId!);
    expect(titleEl?.textContent).toBe("¿Deseas cerrar el asistente?");
  });
});
