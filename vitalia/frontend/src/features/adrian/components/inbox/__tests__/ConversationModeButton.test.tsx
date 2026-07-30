// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * ConversationModeButton.test.tsx — T-5 tests.
 *
 * SC-5: "Modo conversación" collapses Valeria → inbox full width.
 * RN-12: toggle-off restores priorValeriaState from inbox-store.
 *
 * T-V2 (platform-lift-shell-chrome-ui-kit): migrated from useShellStore (legacy)
 * to useShellStoreKit (kit API). Mock updated to supervisorOpen/openSupervisor/
 * collapseSupervisor (matching the canonical kit store API).
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach, type Mock } from "vitest";
import { render, screen } from "@testing-library/react";

// Mocks — kit store API (T-V2)
const mockOpenSupervisor = vi.fn();
const mockCollapseSupervisor = vi.fn();
const mockSetPriorValeriaState = vi.fn();

vi.mock("@/stores/shell-store", () => {
  return {
    useShellStoreKit: vi.fn(
      (
        selector: (s: {
          supervisorOpen: string;
          openSupervisor: typeof mockOpenSupervisor;
          collapseSupervisor: typeof mockCollapseSupervisor;
        }) => unknown,
      ) =>
        selector({
          supervisorOpen: "chat",
          openSupervisor: mockOpenSupervisor,
          collapseSupervisor: mockCollapseSupervisor,
        }),
    ),
  };
});

vi.mock("../../../store/inbox-store", () => {
  return {
    useInboxStore: vi.fn(
      (selector: (s: { priorValeriaState: string | null; setPriorValeriaState: typeof mockSetPriorValeriaState }) => unknown) =>
        selector({
          priorValeriaState: null,
          setPriorValeriaState: mockSetPriorValeriaState,
        }),
    ),
  };
});

import { ConversationModeButton } from "../ConversationModeButton";

describe("ConversationModeButton — SC-5 full-canvas (RN-12)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("test_renders: has data-testid=conversation-mode-button", () => {
    render(<ConversationModeButton />);
    expect(screen.getByTestId("conversation-mode-button")).toBeDefined();
  });

  it("test_label: shows Modo conversación text", () => {
    render(<ConversationModeButton />);
    const btn = screen.getByTestId("conversation-mode-button");
    expect(btn.textContent).toContain("Modo conversación");
  });

  it("test_aria_pressed_false: aria-pressed is false when supervisor is open (supervisorOpen='chat')", () => {
    render(<ConversationModeButton />);
    const btn = screen.getByTestId("conversation-mode-button");
    expect(btn.getAttribute("aria-pressed")).toBe("false");
  });

  it("test_aria_pressed_true: aria-pressed is true when supervisor is closed (supervisorOpen='closed')", async () => {
    const { useShellStoreKit } = await import("@/stores/shell-store");
    (useShellStoreKit as unknown as Mock).mockImplementation(
      (
        selector: (s: {
          supervisorOpen: string;
          openSupervisor: typeof mockOpenSupervisor;
          collapseSupervisor: typeof mockCollapseSupervisor;
        }) => unknown,
      ) =>
        selector({
          supervisorOpen: "closed",
          openSupervisor: mockOpenSupervisor,
          collapseSupervisor: mockCollapseSupervisor,
        }),
    );
    render(<ConversationModeButton />);
    const btn = screen.getByTestId("conversation-mode-button");
    expect(btn.getAttribute("aria-pressed")).toBe("true");
  });

  it("test_no_voseo: no voseo in button text (Spanish neutro)", () => {
    render(<ConversationModeButton />);
    const text = screen.getByTestId("conversation-mode-button").textContent ?? "";
    expect(text).not.toMatch(/tenés|podés|hacé|mirá|dejá|poné|usá|volvé|abrí/);
  });

  it("test_button_type: button has type=button (no form submit)", () => {
    render(<ConversationModeButton />);
    const btn = screen.getByTestId("conversation-mode-button");
    expect(btn.getAttribute("type")).toBe("button");
  });
});
