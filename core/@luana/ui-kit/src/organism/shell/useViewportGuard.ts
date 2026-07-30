// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * useViewportGuard — brand-agnostic viewport sizing contract (T-K2 port).
 *
 * STORE-INERT BY DESIGN (verbatim from vitalia useViewportGuard):
 * The shell state machine is binary (`supervisorOpen: "closed" | "chat"`) plus
 * an additive `historyOpen` flag and an INDEPENDENT `mobileDrawerOpen` slice
 * (D5). There is no intermediate "narrow-but-open" state to auto-clamp the store
 * to, and the mobile drawer is governed SOLELY by the burger / close actions —
 * never by the viewport. So this hook NEVER mutates supervisorOpen / historyOpen
 * / mobileDrawerOpen. Auto-mutating the store from a viewport effect was the root
 * cause of Bug #2 (burger flipping the desktop slice) and would break RN-5 /
 * RN-11 (history must never re-open on resize/reload).
 *
 * What this hook OWNS: the breakpoint constants the layout consumes for its CSS
 * gating + the ResizeObserver clamp of the supervisor panel.
 *
 * The hook itself is intentionally a no-op effect: it exists as the documented
 * home of the contract + a stable hook for the layout to call unconditionally
 * (D3 stable hook count — never conditionally mount/skip it by viewport).
 */

import { useEffect } from "react";

/**
 * Clamp floor (px) for the supervisor panel width in the inline split window
 * [1024, 1280). The panel never shrinks below this; consumed by the layout's
 * ResizeObserver/min-size clamp. (was VALERIA_MIN_PX = 320.)
 */
export const SUPERVISOR_MIN_PX = 320;

/**
 * Drawer breakpoint (px). Below this viewport width the supervisor renders as a
 * drawer/overlay (role=dialog, focus-trap, backdrop, Esc, burger-driven via the
 * independent `mobileDrawerOpen` slice). At/above it the supervisor is an inline
 * panel.
 */
export const DRAWER_BREAKPOINT = 1024;

/**
 * Inline-split breakpoint (px). At/above this width the shell renders the fixed
 * 30/70 supervisor/agent split with the 280px history push. In [1024, 1280) the
 * supervisor is still inline but clamped to SUPERVISOR_MIN_PX.
 */
export const INLINE_SPLIT_MIN_VIEWPORT = 1280;

/**
 * useViewportGuard — store-inert viewport hook.
 *
 * Call this ONCE, unconditionally, from the layout client (never gate the call
 * by viewport — that would change the hook count and trip "Rendered more
 * hooks"). It does NOT mutate the shell store; viewport sizing is handled by CSS
 * gating + the layout's clamp using the exported constants.
 */
export function useViewportGuard(): void {
  useEffect(() => {
    // Intentionally inert: the binary machine has no viewport-driven store
    // mutation. Sizing is CSS-gated + clamped in the layout via the exported
    // constants above. Keeping this effect (empty) preserves a stable hook for
    // the layout and documents the contract home.
    return;
  }, []);
}
