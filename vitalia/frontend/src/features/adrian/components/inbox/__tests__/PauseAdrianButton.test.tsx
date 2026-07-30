/**
 * PauseAdrianButton.test.tsx — Unit tests for PauseAdrianButton.
 *
 * Tests:
 *   - Not-paused state: button enabled, opens modal on click
 *   - Paused state: button disabled
 *   - aria-label matches INBOX_COPY per state
 *   - Modal confirm calls mutation
 *   - Modal cancel closes without mutation
 *
 * usePauseAdrian mocked via vi.mock.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PauseAdrianButton } from "../PauseAdrianButton";
import { INBOX_COPY } from "../../../lib/copy";

// Mock usePauseAdrian
const mockMutate = vi.fn();
vi.mock("../../../api/use-pause-adrian", () => ({
  usePauseAdrian: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
  PERMANENT_PAUSE_MINUTES: 52_560_000,
}));

describe("PauseAdrianButton — not paused state", () => {
  beforeEach(() => {
    mockMutate.mockReset();
  });

  it("renders with data-testid=pause-adrian-button", () => {
    render(<PauseAdrianButton conversationId="conv-1" pauseUntil={null} />);
    expect(screen.getByTestId("pause-adrian-button")).toBeDefined();
  });

  it("button is enabled when pauseUntil is null", () => {
    render(<PauseAdrianButton conversationId="conv-1" pauseUntil={null} />);
    const btn = screen.getByTestId("pause-adrian-button") as HTMLButtonElement;
    expect(btn.disabled).toBe(false);
  });

  it("aria-label is INBOX_COPY.pauseAgent.button when not paused", () => {
    render(<PauseAdrianButton conversationId="conv-1" pauseUntil={null} />);
    const btn = screen.getByTestId("pause-adrian-button");
    expect(btn.getAttribute("aria-label")).toBe(INBOX_COPY.pauseAgent.button);
  });

  it("opens confirmation modal on click", () => {
    render(<PauseAdrianButton conversationId="conv-1" pauseUntil={null} />);
    expect(screen.queryByTestId("pause-adrian-modal")).toBeNull();
    fireEvent.click(screen.getByTestId("pause-adrian-button"));
    expect(screen.getByTestId("pause-adrian-modal")).toBeDefined();
  });

  it("modal cancel closes without calling mutate", () => {
    render(<PauseAdrianButton conversationId="conv-1" pauseUntil={null} />);
    fireEvent.click(screen.getByTestId("pause-adrian-button"));
    fireEvent.click(screen.getByTestId("pause-modal-cancel"));
    expect(screen.queryByTestId("pause-adrian-modal")).toBeNull();
    expect(mockMutate).not.toHaveBeenCalled();
  });

  it("modal '60 min' calls mutate with conversationId + duration", () => {
    render(<PauseAdrianButton conversationId="conv-1" pauseUntil={null} />);
    fireEvent.click(screen.getByTestId("pause-adrian-button"));
    fireEvent.click(screen.getByTestId("pause-modal-60"));
    expect(mockMutate).toHaveBeenCalledTimes(1);
    expect(mockMutate).toHaveBeenCalledWith(
      expect.objectContaining({ conversationId: "conv-1", durationMinutes: 60 }),
      expect.anything(),
    );
  });

  it("modal 'permanente' calls mutate with a large duration", () => {
    render(<PauseAdrianButton conversationId="conv-1" pauseUntil={null} />);
    fireEvent.click(screen.getByTestId("pause-adrian-button"));
    fireEvent.click(screen.getByTestId("pause-modal-permanent"));
    expect(mockMutate).toHaveBeenCalledTimes(1);
    expect(mockMutate).toHaveBeenCalledWith(
      expect.objectContaining({ conversationId: "conv-1" }),
      expect.anything(),
    );
    const arg = mockMutate.mock.calls[0][0] as { durationMinutes: number };
    expect(arg.durationMinutes).toBeGreaterThan(60);
  });
});

describe("PauseAdrianButton — paused state", () => {
  it("button is disabled when pauseUntil is in the future", () => {
    const futureDate = new Date(Date.now() + 60 * 60 * 1000).toISOString();
    render(
      <PauseAdrianButton conversationId="conv-1" pauseUntil={futureDate} />,
    );
    const btn = screen.getByTestId("pause-adrian-button") as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it("aria-label is INBOX_COPY.pauseAgent.buttonActive when paused", () => {
    const futureDate = new Date(Date.now() + 60 * 60 * 1000).toISOString();
    render(
      <PauseAdrianButton conversationId="conv-1" pauseUntil={futureDate} />,
    );
    const btn = screen.getByTestId("pause-adrian-button");
    expect(btn.getAttribute("aria-label")).toBe(
      INBOX_COPY.pauseAgent.buttonActive,
    );
  });

  it("button is enabled when pauseUntil is in the past (expired)", () => {
    const pastDate = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    render(<PauseAdrianButton conversationId="conv-1" pauseUntil={pastDate} />);
    const btn = screen.getByTestId("pause-adrian-button") as HTMLButtonElement;
    expect(btn.disabled).toBe(false);
  });
});
