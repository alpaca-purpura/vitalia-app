// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s5-TBD
"use client";

/**
 * useKeyboardShortcuts.ts — Generic hardened keyboard shortcut hook.
 *
 * T-1 vitalia-fase1-valeria-rail-history (F1-S5)
 *
 * Design contract decisions (03-arch.md § 2.3 + 01-spec.md § 0 D4):
 *
 * ShortcutsMap key format:
 *   - Bare key: "r", "f", "c", "Escape"  — simple key match (no modifier)
 *   - Modifier key: "mod+k"               — Cmd (Mac) OR Ctrl (Win/Linux)
 *
 * Hardened guard — SKIP handler if:
 *   1. e.isComposing === true         → IME composition in progress
 *   2. target is INPUT / TEXTAREA     → user is typing
 *   3. target is [contenteditable]    → user is editing inline
 *   4. any ancestor has [contenteditable=true] or [role="textbox"]
 *
 * EXCEPTION (bypass): modifier shortcuts (mod+key) BYPASS the input guard.
 *   Cmd+K must fire even inside a composer INPUT (focus-jump intent).
 *
 * Cross-platform mod key: event.metaKey (Mac) || event.ctrlKey (Windows/Linux).
 *
 * Cleanup contract:
 *   - addEventListener('keydown', handler) on mount
 *   - removeEventListener in useEffect return (cleanup function)
 *   - Dependency array: [shortcuts] — re-attach if shortcuts identity changes
 *
 * LIFT CANDIDATE: this hook has zero brand-specific logic. Promote to
 * core/@luana/hooks/ when a second consumer (Nicolify/Comunify/Lupulo)
 * needs keyboard shortcuts. Decision: /pm-luana post F1-S5 merge.
 *
 * No default export (FSD-Lite arch test enforce).
 * No user-facing strings in this file (spanish-text.md rule N/A).
 * downstream-regression-na: brand-local hook; first and only consumer F1-S5.
 */

import { useEffect } from "react";

/** Map from shortcut string to callback. */
export type ShortcutsMap = Record<string, () => void>;

/**
 * Returns true if the shortcut key string contains a modifier prefix.
 * Currently only "mod+" is supported.
 */
function hasModifier(shortcutKey: string): boolean {
  return shortcutKey.startsWith("mod+");
}

/**
 * Returns true if the keyboard event has the platform modifier key pressed.
 * Mac: metaKey (Cmd). Windows/Linux: ctrlKey (Ctrl).
 */
function isModifierActive(e: KeyboardEvent): boolean {
  return e.metaKey || e.ctrlKey;
}

/**
 * Returns true if the event target (or any ancestor) represents an editable
 * context where bare key shortcuts should be swallowed.
 *
 * Checks:
 *  - tagName INPUT or TEXTAREA
 *  - element or ancestor has contenteditable="true"
 *  - element or ancestor has role="textbox"
 */
function isInEditableContext(target: EventTarget | null): boolean {
  if (!(target instanceof Element)) return false;

  const tag = (target as Element).tagName;
  if (tag === "INPUT" || tag === "TEXTAREA") return true;

  // Walk up the DOM to detect contenteditable / role=textbox ancestors
  let node: Element | null = target as Element;
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
 * Registers keyboard shortcuts on the window while the component is mounted.
 *
 * @param shortcuts - Map from shortcut key (e.g., "r", "Escape", "mod+k")
 *                    to callback function.
 *
 * @example
 * useKeyboardShortcuts({
 *   r: () => setValeriaState('rail'),
 *   f: () => setValeriaState('full'),
 *   c: () => setValeriaState('collapsed'),
 *   Escape: () => setValeriaState('rail'),
 *   'mod+k': () => document.getElementById('valeria-composer-placeholder')?.focus(),
 * });
 */
export function useKeyboardShortcuts(shortcuts: ShortcutsMap): void {
  useEffect(() => {
    function handleKeydown(e: KeyboardEvent): void {
      // Guard 1: skip IME composition events
      if (e.isComposing) return;

      // Determine if this event carries the platform modifier key
      const modActive = isModifierActive(e);
      const inEditable = isInEditableContext(e.target);

      for (const [shortcutKey, handler] of Object.entries(shortcuts)) {
        const shortcutHasModifier = hasModifier(shortcutKey);

        // Guard 2: skip bare-key shortcuts when focus is inside an editable context.
        // EXCEPTION: modifier shortcuts bypass this guard (Cmd+K must work inside inputs).
        if (inEditable && !shortcutHasModifier) continue;

        if (shortcutHasModifier) {
          // mod+k format: require modifier key + the character after "mod+"
          const key = shortcutKey.slice(4); // strip "mod+"
          if (modActive && e.key === key) {
            handler();
            break;
          }
        } else {
          // Bare key: exact match, no modifier required
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
    // Re-attach when shortcuts identity changes (new dict = new reference).
    // Dependency array intentionally contains only [shortcuts] — all other
    // variables (isInEditableContext, isModifierActive, hasModifier) are
    // stable module-level functions, not closures.
  }, [shortcuts]);
}
