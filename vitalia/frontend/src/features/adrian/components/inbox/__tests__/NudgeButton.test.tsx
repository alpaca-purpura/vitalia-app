// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * NudgeButton.test.tsx — T-5 tests.
 *
 * SC-6: "Dar empujón" button + confirm flow.
 * Verifies nudge button renders + shows confirm on click + cancel works.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// Mock the useNudge hook
const mockMutate = vi.fn();
vi.mock("../../../api/use-nudge", () => ({
  useNudge: vi.fn(() => ({
    mutate: mockMutate,
    isPending: false,
  })),
}));

// Mock sonner toast
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

import { NudgeButton } from "../NudgeButton";

describe("NudgeButton — SC-6 empujón flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("test_renders: has data-testid=nudge-button", () => {
    render(<NudgeButton conversationId="conv-123" />);
    expect(screen.getByTestId("nudge-button")).toBeDefined();
  });

  it("test_label: shows Dar empujón text", () => {
    render(<NudgeButton conversationId="conv-123" />);
    const btn = screen.getByTestId("nudge-button");
    expect(btn.textContent).toContain("Dar empujón");
  });

  it("test_enabled_by_default: button is enabled by default", () => {
    render(<NudgeButton conversationId="conv-123" />);
    const btn = screen.getByTestId("nudge-button") as HTMLButtonElement;
    expect(btn.disabled).toBe(false);
  });

  it("test_disabled: button is disabled when isEnabled=false", () => {
    render(<NudgeButton conversationId="conv-123" isEnabled={false} />);
    const btn = screen.getByTestId("nudge-button") as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it("test_confirm_shows: clicking nudge button shows confirm UI", () => {
    render(<NudgeButton conversationId="conv-123" />);
    fireEvent.click(screen.getByTestId("nudge-button"));
    expect(screen.getByTestId("nudge-confirm")).toBeDefined();
  });

  it("test_cancel: clicking cancel hides confirm UI", () => {
    render(<NudgeButton conversationId="conv-123" />);
    fireEvent.click(screen.getByTestId("nudge-button"));
    // Confirm is now visible
    expect(screen.getByTestId("nudge-confirm")).toBeDefined();
    // Click cancel
    fireEvent.click(screen.getByTestId("nudge-confirm-cancel"));
    // Original button should be back
    expect(screen.getByTestId("nudge-button")).toBeDefined();
    expect(screen.queryByTestId("nudge-confirm")).toBeNull();
  });

  it("test_confirm_calls_mutation: clicking confirm-yes calls mutate", () => {
    render(<NudgeButton conversationId="conv-abc" />);
    fireEvent.click(screen.getByTestId("nudge-button"));
    fireEvent.click(screen.getByTestId("nudge-confirm-yes"));
    expect(mockMutate).toHaveBeenCalledTimes(1);
    expect(mockMutate).toHaveBeenCalledWith(
      { conversationId: "conv-abc" },
      expect.any(Object),
    );
  });

  it("test_no_voseo: button text contains no voseo", () => {
    render(<NudgeButton conversationId="conv-123" />);
    const text = screen.getByTestId("nudge-button").textContent ?? "";
    expect(text).not.toMatch(/tenés|podés|hacé|mirá|dejá|poné/);
  });

  it("test_button_type: button has type=button", () => {
    render(<NudgeButton conversationId="conv-123" />);
    expect(screen.getByTestId("nudge-button").getAttribute("type")).toBe("button");
  });
});
