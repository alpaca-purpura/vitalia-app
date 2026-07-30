"use client";

import { useEffect, useState } from "react";

import { useViewport } from "./use-viewport";

/**
 * Returns the current copilot/assistant sidebar offset in pixels — so overlay atoms
 * (Dialog, Sheet, AlertDialog, DetailPanel) can shift to avoid covering an open
 * assistant panel.
 *
 * ★ Decoupled (core-ds-foundation, caught live: /showcase 500 in vitalia).
 * Previously this hook hard-imported `@/features/copilot/lib/copilot-shell-widths` +
 * `@/features/copilot/store/copilot-store` — paths that only resolve inside ONE specific
 * brand app. Because `@luana/ui-kit`'s barrel re-exports those 4 atoms, the app-coupling
 * made the ENTIRE ui-kit unconsumable in any brand lacking `@/features/copilot/*` (i.e. all
 * of them today — the paths don't exist in nicolify/vitalia/comunify). A shared package
 * cannot know a consumer's copilot store.
 *
 * New contract (dependency inversion via CSS variable):
 * the consuming app's copilot/assistant shell sets `--copilot-offset` (px) on the document
 * root; this hook reads it and returns `0` when absent. So @luana/ui-kit is consumable in
 * ANY app — with or without a copilot — and apps that DO have one opt in by setting the var.
 *
 * - No `--copilot-offset` set (or mobile) → 0 (atom centers normally).
 * - Var set by the shell                  → that pixel value.
 */
export function useCopilotOffset(): number {
  const { isMobile } = useViewport();
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    if (isMobile) {
      setOffset(0);
      return;
    }
    if (typeof document === "undefined") return;

    const root = document.documentElement;
    const read = () => {
      const raw = getComputedStyle(root).getPropertyValue("--copilot-offset").trim();
      setOffset(Number.parseInt(raw, 10) || 0);
    };

    read();
    // React to the shell toggling the sidebar (the var changes on the root).
    const observer = new MutationObserver(read);
    observer.observe(root, { attributes: true, attributeFilter: ["style", "class"] });
    return () => observer.disconnect();
  }, [isMobile]);

  return offset;
}
