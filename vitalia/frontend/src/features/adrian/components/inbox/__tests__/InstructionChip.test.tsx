// cap: adrian.inbox
/**
 * InstructionChip.test.tsx — Tests for InstructionChip component.
 *
 * SC-8: chip shows active instruction + edit/clear controls.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { InstructionChip } from "../InstructionChip";
import { INBOX_COPY } from "../../../lib/copy";

const copy = INBOX_COPY.instruction;

describe("InstructionChip", () => {
  it("shows the chip prefix and instruction text", () => {
    render(
      <InstructionChip
        activeInstruction="Ofrécele 10% de descuento"
        onEdit={vi.fn()}
        onClear={vi.fn()}
      />,
    );
    expect(screen.getByText(copy.chipPrefix)).toBeInTheDocument();
    expect(screen.getByText("Ofrécele 10% de descuento")).toBeInTheDocument();
  });

  it("calls onEdit with instruction text when Editar clicked", () => {
    const onEdit = vi.fn();
    render(
      <InstructionChip
        activeInstruction="Ofrécele 10% de descuento"
        onEdit={onEdit}
        onClear={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: copy.chipEditAriaLabel }));
    expect(onEdit).toHaveBeenCalledWith("Ofrécele 10% de descuento");
  });

  it("calls onClear when ✕ clicked", () => {
    const onClear = vi.fn();
    render(
      <InstructionChip
        activeInstruction="Ofrécele 10% de descuento"
        onEdit={vi.fn()}
        onClear={onClear}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: copy.chipClearAriaLabel }));
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it("disables both buttons when isPending=true", () => {
    render(
      <InstructionChip
        activeInstruction="Test"
        isPending
        onEdit={vi.fn()}
        onClear={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: copy.chipEditAriaLabel }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: copy.chipClearAriaLabel }),
    ).toBeDisabled();
  });
});
