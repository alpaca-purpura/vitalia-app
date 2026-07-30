// cap: shell-organism.shell-vitalia
// story-origin: platform-lift-shell-chrome-ui-kit T-V2
/**
 * shell-store.ts — Shell state store (T-V2 cleanup).
 * platform-lift-shell-chrome-ui-kit T-V2
 *
 * T-V1 introduced a dual-store export pattern for zero-downtime chrome handoff.
 * T-V2 completes the lift: chrome deleted, legacy store removed, canonical store
 * exposed as `useShellStore` for convenience (same underlying kit factory).
 *
 * Single store (kit API — generic, supervisorOpen / splitPct):
 *   storageKey: 'vitalia-shell-state'  (SC-6 conserved — canonical key)
 *   Consumed by layout.tsx → ShellLayout from @luana/ui-kit.
 *   Also used by ConversationModeButton (supervisorOpen / openSupervisor / collapseSupervisor).
 *
 * SC-6: The canonical key 'vitalia-shell-state' is conserved (e2e + legacy migration).
 *
 * Named exports only — no default export (FSD-Lite enforce).
 * HIPAA-lite: not_applicable — shell layout state, no PHI.
 * No Clerk Organizations — MEMORY.md::no-clerk-organizations 2026-05-20.
 *
 * downstream-regression-na: brand-local store; no cross-brand consumers
 */

import { createShellStore } from "@luana/ui-kit";
import type { ShellStoreState } from "@luana/ui-kit";

// ── Canonical storage key (SC-6 — conserved for e2e + migration) ─────────────
/** Canonical shell state key (SC-6). Used by the kit store. */
export const SHELL_STORAGE_KEY = "vitalia-shell-state" as const;
/**
 * T-V2: bumped from 1 → 2 so that Zustand calls migrate() for stored v1 data
 * that uses vitalia-specific field names (valeriaOpen/valeriaPct).
 *
 * Without this bump, Zustand skips migrate() for stored v1 (version matches)
 * and falls through to merge() → sanitizePersistedSlice, which only recognises
 * the generic supervisorOpen field and silently falls back to 'chat'.
 */
const SHELL_STORE_VERSION = 2;

// ─────────────────────────────────────────────────────────────────────────────
// Kit store (generic API — supervisorOpen / splitPct)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Migrate legacy persisted state → kit generic shape.
 * Handles both v0 (legacy collapsed/rail/full) and v1 (valeriaOpen/valeriaPct
 * or supervisorOpen/splitPct).
 */
function migrateShellStateKit(
  persisted: unknown,
  version: number,
): Partial<ShellStoreState> {
  const fallback: Partial<ShellStoreState> = {
    supervisorOpen: "chat",
    splitPct: null,
    mobileDrawerOpen: false,
  };
  if (persisted === null || typeof persisted !== "object") return fallback;
  const raw = persisted as Record<string, unknown>;

  const toPct = (v: unknown): number | null =>
    typeof v === "number" || v === null ? (v as number | null) : null;
  const toBool = (v: unknown): boolean =>
    typeof v === "boolean" ? v : false;

  if (version < 1) {
    const splitPct = toPct(raw.valeriaPct);
    const mobileDrawerOpen = toBool(raw.mobileDrawerOpen);
    switch (raw.valeriaState) {
      case "collapsed":
        return { supervisorOpen: "closed", splitPct, mobileDrawerOpen };
      case "rail":
      case "full":
        return { supervisorOpen: "chat", splitPct, mobileDrawerOpen };
      default:
        console.warn(
          `[shell-store] Unknown v0 valeriaState "${String(raw.valeriaState)}"; falling back to defaults.`,
        );
        return { ...fallback, splitPct, mobileDrawerOpen };
    }
  }

  // v1 / v2 — map vitalia-specific field names → generic kit names.
  // valeriaOpen was the vitalia-specific field name before T-V2 generic renaming.
  const splitPct = toPct(raw.splitPct ?? raw.valeriaPct);
  const mobileDrawerOpen = toBool(raw.mobileDrawerOpen);
  const rawOpen = raw.supervisorOpen ?? raw.valeriaOpen;
  if (rawOpen !== "closed" && rawOpen !== "chat") {
    console.warn(
      `[shell-store] Unknown supervisorOpen/valeriaOpen "${String(rawOpen)}" in persisted state; falling back to defaults.`,
    );
    return { ...fallback, splitPct, mobileDrawerOpen };
  }
  return {
    supervisorOpen: rawOpen as "closed" | "chat",
    splitPct,
    mobileDrawerOpen,
  };
}

/**
 * useShellStoreKit — generic kit API (supervisorOpen / splitPct).
 *
 * Used by layout.tsx to wire ShellLayout from @luana/ui-kit.
 * storageKey 'vitalia-shell-state' — canonical SC-6 key.
 */
export const useShellStoreKit = createShellStore({
  storageKey: SHELL_STORAGE_KEY,
  version: SHELL_STORE_VERSION,
  migrate: migrateShellStateKit,
});

