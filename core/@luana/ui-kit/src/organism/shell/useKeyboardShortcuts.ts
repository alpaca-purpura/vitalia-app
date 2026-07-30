// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * useKeyboardShortcuts — generic hardened keyboard shortcut hook.
 * T-K2 port of vitalia useKeyboardShortcuts (F1-S5 T-1) — ZERO brand logic.
 *
 * ShortcutsMap key format:
 *   - Bare key:     "r", "f", "c", "Escape"  — simple key match (no modifier)
 *   - Modifier key: "mod+k"                  — Cmd (Mac) OR Ctrl (Win/Linux)
 *
 * Hardened guard — SKIP handler if:
 *   1. e.isComposing === true       → IME composition in progress
 *   2. target is INPUT / TEXTAREA   → user is typing
 *   3. target is [contenteditable]  → user is editing inline
 *   4. any ancestor [contenteditable=true] or [role="textbox"]
 *
 * EXCEPTION (bypass): modifier shortcuts (mod+key) BYPASS the input guard
 * — Cmd+K must fire even inside a composer INPUT (focus-jump intent).
 *
 * Cross-platform mod key: event.metaKey (Mac) || event.ctrlKey (Win/Linux).
 *
 * Cleanup: addEventListener on mount, removeEventListener on unmount.
 * Dependency array [shortcuts] — re-attach when the dict identity changes.
 */

import { useEffect } from "react";

/** Map from shortcut string to callback. */
export type ShortcutsMap = Record<string, () => void>;

/** True if the shortcut key string carries a "mod+" prefix. */
function hasModifier(shortcutKey: string): boolean {
  return shortcutKey.startsWith("mod+");
}

/** True if the event has the platform modifier (Cmd on Mac, Ctrl elsewhere). */
function isModifierActive(e: KeyboardEvent): boolean {
  return e.metaKey || e.ctrlKey;
}

/**
 * True if the event target (or any ancestor) is an editable context where
 * bare-key shortcuts should be swallowed (INPUT/TEXTAREA/contenteditable/
 * role=textbox).
 */
function isInEditableContext(target: EventTarget | null): boolean {
  if (!(target instanceof Element)) return false;

  const tag = target.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA") return true;

  let node: Element | null = target;
  while (node !== null) {
    if (
      node.getAttribute("contenteditable") === "true" ||
      (node instanceof HTMLElement && node.isContentEditable) ||
      node.getAttribute("role") === "textbox"
    ) {
      return true;
    }
    node = node.parentElement;
  }

  return false;
}

/**
 * Registers keyboard shortcuts on window while the component is mounted.
 *
 * @param shortcuts - Map from shortcut key (e.g., "r", "Escape", "mod+k") to callback.
 */
export function useKeyboardShortcuts(shortcuts: ShortcutsMap): void {
  useEffect(() => {
    function handleKeydown(e: KeyboardEvent): void {
      // Guard 1: skip IME composition events.
      if (e.isComposing) return;

      const modActive = isModifierActive(e);
      const inEditable = isInEditableContext(e.target);

      for (const [shortcutKey, handler] of Object.entries(shortcuts)) {
        const shortcutHasModifier = hasModifier(shortcutKey);

        // Guard 2: skip bare-key shortcuts inside an editable context.
        // EXCEPTION: modifier shortcuts bypass this guard.
        if (inEditable && !shortcutHasModifier) continue;

        if (shortcutHasModifier) {
          const key = shortcutKey.slice(4); // strip "mod+"
          if (modActive && e.key === key) {
            handler();
            break;
          }
        } else {
          if (!modActive && e.key === shortcutKey) {
            handler();
            break;
          }
        }
      }
    }

    window.addEventListener("keydown", handleKeydown, { passive: true });

    return () => {
      window.removeEventListener("keydown", handleKeydown, {
        passive: true,
      } as EventListenerOptions);
    };
    // Re-attach when the shortcuts dict identity changes (new ref = new dict).
  }, [shortcuts]);
}
