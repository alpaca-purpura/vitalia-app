// canon: design-system-canon.md §2.6 · story-origin: vitalia-fase2-mateo-nueva-cita (P-0)
/**
 * FormActionBar.test.tsx — Validator for the sticky explicit-submit bar (@luana/ui-kit).
 *
 * Covers:
 *   - onCancel / onSubmit fire on click
 *   - submitting disables the submit button (+ aria-busy)
 *   - submitDisabled disables the submit button
 *   - cancel button only renders when onCancel is provided
 *   - accent applies the agent-token background (token-driven, never hex)
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { FormActionBar } from "../FormActionBar";

describe("FormActionBar", () => {
  it("fires onCancel and onSubmit on click", () => {
    const onCancel = vi.fn();
    const onSubmit = vi.fn();
    render(
      <FormActionBar
        submitLabel="Crear cita"
        onCancel={onCancel}
        onSubmit={onSubmit}
        hint="Sin guardar todavía"
      />,
    );

    fireEvent.click(screen.getByTestId("form-action-bar-submit"));
    expect(onSubmit).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByTestId("form-action-bar-cancel"));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("disables the submit button while submitting (+ aria-busy + spinner)", () => {
    const onSubmit = vi.fn();
    render(<FormActionBar submitLabel="Crear cita" onSubmit={onSubmit} submitting />);

    const submit = screen.getByTestId("form-action-bar-submit");
    expect(submit).toBeDisabled();
    expect(submit).toHaveAttribute("aria-busy", "true");

    // Click does nothing while disabled.
    fireEvent.click(submit);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("disables the submit button when submitDisabled (validation block)", () => {
    const onSubmit = vi.fn();
    render(<FormActionBar submitLabel="Crear cita" onSubmit={onSubmit} submitDisabled />);

    const submit = screen.getByTestId("form-action-bar-submit");
    expect(submit).toBeDisabled();
    fireEvent.click(submit);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("renders the cancel button only when onCancel is provided", () => {
    const { rerender } = render(<FormActionBar submitLabel="Crear cita" />);
    expect(screen.queryByTestId("form-action-bar-cancel")).not.toBeInTheDocument();

    rerender(<FormActionBar submitLabel="Crear cita" onCancel={vi.fn()} />);
    expect(screen.getByTestId("form-action-bar-cancel")).toBeInTheDocument();
  });

  it("uses the default Spanish-neutro cancel label", () => {
    render(<FormActionBar submitLabel="Crear cita" onCancel={vi.fn()} />);
    expect(screen.getByTestId("form-action-bar-cancel")).toHaveTextContent("Cancelar");
  });

  it("applies the agent-color accent via a token (never a hex)", () => {
    render(<FormActionBar submitLabel="Crear cita" onSubmit={vi.fn()} accent="mateo" />);
    const submit = screen.getByTestId("form-action-bar-submit");
    expect(submit.style.backgroundColor).toBe("hsl(var(--agent-mateo))");
  });
});
