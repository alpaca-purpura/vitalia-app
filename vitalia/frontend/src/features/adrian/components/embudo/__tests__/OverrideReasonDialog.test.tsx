// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * OverrideReasonDialog.test.tsx — RED-first tests for OverrideReasonDialog (T-FE-2).
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { OverrideReasonDialog } from "../OverrideReasonDialog";

describe("OverrideReasonDialog", () => {
  const defaultProps = {
    open: true,
    fromStage: "interesado" as const,
    toStage: "consulta_agendada" as const,
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  };

  it("renders dialog when open=true", () => {
    render(<OverrideReasonDialog {...defaultProps} />);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("shows reason textarea with label", () => {
    render(<OverrideReasonDialog {...defaultProps} />);
    expect(screen.getByLabelText(/razón/i)).toBeInTheDocument();
  });

  it("submit button is disabled with empty reason", () => {
    render(<OverrideReasonDialog {...defaultProps} />);
    const submitBtn = screen.getByRole("button", { name: /mover a/i });
    expect(submitBtn).toBeDisabled();
  });

  it("calls onConfirm with reason on valid submit", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    render(<OverrideReasonDialog {...defaultProps} onConfirm={onConfirm} />);
    const textarea = screen.getByLabelText(/razón/i);
    await user.type(textarea, "coordiné por teléfono");
    const submitBtn = screen.getByRole("button", { name: /mover a/i });
    await user.click(submitBtn);
    await waitFor(() =>
      expect(onConfirm).toHaveBeenCalledWith({
        reason: "coordiné por teléfono",
        toStage: "consulta_agendada",
      })
    );
  });

  it("calls onCancel when cancel button clicked", async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(<OverrideReasonDialog {...defaultProps} onCancel={onCancel} />);
    const cancelBtn = screen.getByRole("button", { name: /cancelar/i });
    await user.click(cancelBtn);
    expect(onCancel).toHaveBeenCalled();
  });

  it("does not render when open=false", () => {
    render(<OverrideReasonDialog {...defaultProps} open={false} />);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
