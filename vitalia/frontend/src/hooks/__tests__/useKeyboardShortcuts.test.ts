/**
 * useKeyboardShortcuts.test.ts — TDD RED → GREEN
 *
 * T-1 vitalia-fase1-valeria-rail-history
 *
 * 11 tests cubriendo:
 * 1. dispatches bare lowercase key handler ('r' → handler called)
 * 2. dispatches Escape exact match handler
 * 3. dispatches mod+k via metaKey (Mac)
 * 4. dispatches mod+k via ctrlKey (Windows/Linux cross-platform)
 * 5. skips dispatch when focus en INPUT
 * 6. skips dispatch when focus en TEXTAREA
 * 7. skips dispatch when focus en [contenteditable=true]
 * 8. modifier shortcuts (Cmd+K) BYPASS focus-in-input guard
 * 9. skips dispatch when e.isComposing=true (IME composition)
 * 10. removeEventListener on unmount (cleanup contract)
 * 11. registers fresh handler when shortcuts dict identity changes
 */

import { renderHook } from "@testing-library/react";
import { useKeyboardShortcuts } from "../useKeyboardShortcuts";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeInputElement(
  tagName: "INPUT" | "TEXTAREA" = "INPUT",
): HTMLInputElement | HTMLTextAreaElement {
  const el = document.createElement(tagName.toLowerCase()) as
    | HTMLInputElement
    | HTMLTextAreaElement;
  document.body.appendChild(el);
  el.focus();
  return el;
}

function makeContentEditableElement(): HTMLDivElement {
  const el = document.createElement("div");
  el.setAttribute("contenteditable", "true");
  document.body.appendChild(el);
  el.focus();
  return el;
}

// ---------------------------------------------------------------------------
// Test suite
// ---------------------------------------------------------------------------

describe("useKeyboardShortcuts", () => {
  afterEach(() => {
    // Remove any elements added to body during the test
    document.body.innerHTML = "";
    // Reset focus to body
    document.body.focus();
  });

  // ── Test 1: dispatches bare lowercase key handler ('r' → handler called) ─

  it("calls handler for a bare lowercase key", () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcuts({ r: handler }));

    const event = new KeyboardEvent("keydown", { key: "r", bubbles: true });
    window.dispatchEvent(event);

    expect(handler).toHaveBeenCalledTimes(1);
  });

  // ── Test 2: dispatches Escape exact match handler ──────────────────────

  it("calls handler for Escape key", () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcuts({ Escape: handler }));

    const event = new KeyboardEvent("keydown", {
      key: "Escape",
      bubbles: true,
    });
    window.dispatchEvent(event);

    expect(handler).toHaveBeenCalledTimes(1);
  });

  // ── Test 3: dispatches mod+k via metaKey (Mac) ────────────────────────

  it("calls handler for mod+k via metaKey (Mac)", () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcuts({ "mod+k": handler }));

    const event = new KeyboardEvent("keydown", {
      key: "k",
      metaKey: true,
      bubbles: true,
    });
    window.dispatchEvent(event);

    expect(handler).toHaveBeenCalledTimes(1);
  });

  // ── Test 4: dispatches mod+k via ctrlKey (Windows/Linux) ──────────────

  it("calls handler for mod+k via ctrlKey (Windows/Linux cross-platform)", () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcuts({ "mod+k": handler }));

    const event = new KeyboardEvent("keydown", {
      key: "k",
      ctrlKey: true,
      bubbles: true,
    });
    window.dispatchEvent(event);

    expect(handler).toHaveBeenCalledTimes(1);
  });

  // ── Test 5: skips dispatch when focus en INPUT ─────────────────────────

  it("skips bare key handler when focus is inside an INPUT element", () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcuts({ r: handler }));

    const input = makeInputElement("INPUT");
    input.focus();

    const event = new KeyboardEvent("keydown", { key: "r", bubbles: true });
    Object.defineProperty(event, "target", {
      value: input,
      writable: false,
    });
    window.dispatchEvent(event);

    expect(handler).not.toHaveBeenCalled();
  });

  // ── Test 6: skips dispatch when focus en TEXTAREA ─────────────────────

  it("skips bare key handler when focus is inside a TEXTAREA element", () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcuts({ r: handler }));

    const textarea = makeInputElement("TEXTAREA");
    textarea.focus();

    const event = new KeyboardEvent("keydown", { key: "r", bubbles: true });
    Object.defineProperty(event, "target", {
      value: textarea,
      writable: false,
    });
    window.dispatchEvent(event);

    expect(handler).not.toHaveBeenCalled();
  });

  // ── Test 7: skips dispatch when focus en [contenteditable=true] ────────

  it("skips bare key handler when focus is inside a contenteditable element", () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcuts({ r: handler }));

    const ce = makeContentEditableElement();
    ce.focus();

    const event = new KeyboardEvent("keydown", { key: "r", bubbles: true });
    Object.defineProperty(event, "target", {
      value: ce,
      writable: false,
    });
    window.dispatchEvent(event);

    expect(handler).not.toHaveBeenCalled();
  });

  // ── Test 8: modifier shortcuts (Cmd+K) BYPASS focus-in-input guard ─────

  it("modifier shortcuts bypass the input guard (Cmd+K fires inside INPUT)", () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcuts({ "mod+k": handler }));

    const input = makeInputElement("INPUT");
    input.focus();

    const event = new KeyboardEvent("keydown", {
      key: "k",
      metaKey: true,
      bubbles: true,
    });
    Object.defineProperty(event, "target", {
      value: input,
      writable: false,
    });
    window.dispatchEvent(event);

    expect(handler).toHaveBeenCalledTimes(1);
  });

  // ── Test 9: skips dispatch when e.isComposing=true (IME composition) ───

  it("skips dispatch when e.isComposing is true (IME composition in progress)", () => {
    const handler = vi.fn();
    renderHook(() => useKeyboardShortcuts({ r: handler }));

    const event = new KeyboardEvent("keydown", { key: "r", bubbles: true });
    Object.defineProperty(event, "isComposing", {
      value: true,
      writable: false,
    });
    window.dispatchEvent(event);

    expect(handler).not.toHaveBeenCalled();
  });

  // ── Test 10: removeEventListener on unmount (cleanup contract) ─────────

  it("removes the event listener on unmount (cleanup contract)", () => {
    const addSpy = vi.spyOn(window, "addEventListener");
    const removeSpy = vi.spyOn(window, "removeEventListener");

    const handler = vi.fn();
    const { unmount } = renderHook(() => useKeyboardShortcuts({ r: handler }));

    // Verify addEventListener was called with 'keydown' during mount
    expect(addSpy).toHaveBeenCalledWith(
      "keydown",
      expect.any(Function),
      expect.anything(),
    );

    unmount();

    // Verify removeEventListener was called with 'keydown' during cleanup
    expect(removeSpy).toHaveBeenCalledWith(
      "keydown",
      expect.any(Function),
      expect.anything(),
    );

    addSpy.mockRestore();
    removeSpy.mockRestore();
  });

  // ── Test 11: re-attaches handler when shortcuts dict identity changes ───

  it("re-attaches the event listener when shortcuts identity changes", () => {
    const addSpy = vi.spyOn(window, "addEventListener");
    const removeSpy = vi.spyOn(window, "removeEventListener");

    const handler1 = vi.fn();
    const handler2 = vi.fn();

    const { rerender } = renderHook(
      ({ shortcuts }: { shortcuts: Record<string, () => void> }) =>
        useKeyboardShortcuts(shortcuts),
      {
        initialProps: { shortcuts: { r: handler1 } },
      },
    );

    const addCallsAfterMount = addSpy.mock.calls.filter(
      (c) => c[0] === "keydown",
    ).length;

    // Provide a new shortcuts object identity (simulates re-render with new dict)
    rerender({ shortcuts: { r: handler2 } });

    const addCallsAfterRerender = addSpy.mock.calls.filter(
      (c) => c[0] === "keydown",
    ).length;

    // Must have re-attached (at least one more addEventListener call)
    expect(addCallsAfterRerender).toBeGreaterThan(addCallsAfterMount);

    // And must have removed the old listener
    expect(removeSpy).toHaveBeenCalledWith(
      "keydown",
      expect.any(Function),
      expect.anything(),
    );

    // Verify new handler fires
    const event = new KeyboardEvent("keydown", { key: "r", bubbles: true });
    window.dispatchEvent(event);
    expect(handler2).toHaveBeenCalledTimes(1);
    expect(handler1).not.toHaveBeenCalled();

    addSpy.mockRestore();
    removeSpy.mockRestore();
  });
});
