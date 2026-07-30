// cap: platform.lift-shell-chrome-ui-kit
import {
  createSsrSafePersistedStore,
} from "@luana/hooks/create-ssr-safe-persisted-store";
import type {
  CreateShellStoreOptions,
  ShellPersistedState,
  ShellStore,
  ShellStoreState,
  SupervisorOpen,
} from "./types";

/**
 * createShellStore — generic SSR-safe Zustand store factory for the shell
 * state machine (T-K1). Brand-agnostic port of vitalia's `shell-store.ts`,
 * re-parametrized to neutral naming (RN-2):
 *   valeriaOpen → supervisorOpen, valeriaPct → splitPct.
 *
 * The factory CONSUMES `@luana/hooks/createSsrSafePersistedStore` (RN-8,
 * ADR-vitalia-006) — it never reimplements SSR-safe persistence.
 *
 * The brand instantiates a THIN store, e.g.:
 *   export const useShellStore = createShellStore({
 *     storageKey: 'vitalia-shell-state',   // SC-6 — conserved for e2e
 *     version: 1,
 *     migrate: migrateLegacyShellState,    // brand's legacy → generic shape
 *   });
 *
 * MACHINE (generic):
 *   A=closed   : supervisorOpen 'closed' ⇒ historyOpen forced false (RN-5)
 *   B=chat     : supervisorOpen 'chat', NEVER restores history (RN-6)
 *   C=chat+hist: supervisorOpen 'chat' + historyOpen true (RN-7 additive)
 *
 * Persisted slice (partialize): supervisorOpen + splitPct + mobileDrawerOpen.
 *   - historyOpen is NEVER persisted open (no-clobber, RN-5/11) — always starts closed.
 *   - setters + _hasHydrated NOT persisted (recreated on hydration — Zustand standard).
 *
 * No-clobber hydration (SC-6): the factory `merge` runs on EVERY rehydrate;
 * it sanitizes the current-schema persisted slice and forces historyOpen=false.
 * Pre-hydration storage writes are NO-OP (the @luana/hooks factory handles that).
 */

const DEFAULT_VERSION = 1;

/** Sanitize a current-shape persisted slice on rehydrate — coerce invalid → fallback + warn (SC-6). */
function sanitizePersistedSlice(raw: Record<string, unknown>): ShellPersistedState {
  const fallback: ShellPersistedState = {
    supervisorOpen: "chat",
    splitPct: null,
    mobileDrawerOpen: false,
  };

  const splitPct =
    typeof raw.splitPct === "number" || raw.splitPct === null
      ? (raw.splitPct as number | null)
      : null;
  const mobileDrawerOpen =
    typeof raw.mobileDrawerOpen === "boolean" ? raw.mobileDrawerOpen : false;

  const supervisorOpen = raw.supervisorOpen;
  if (supervisorOpen !== "closed" && supervisorOpen !== "chat") {
    console.warn(
      `[shell-store] Unknown supervisorOpen "${String(
        supervisorOpen,
      )}" in persisted state; falling back to defaults.`,
    );
    return { ...fallback, splitPct, mobileDrawerOpen };
  }

  return { supervisorOpen, splitPct, mobileDrawerOpen };
}

/**
 * Default migrate (used when the brand passes no `migrate`).
 * Validates a current-shape persisted slice; corrupt → fallback + warn.
 * Brands with a legacy shape (e.g. nicolify's luanaState/shellMode/splitState)
 * pass their OWN migrate that maps legacy → Partial<ShellStoreState>.
 */
function defaultMigrate(persisted: unknown, _version: number): Partial<ShellStoreState> {
  if (persisted === null || typeof persisted !== "object") {
    return {};
  }
  const slice = sanitizePersistedSlice(persisted as Record<string, unknown>);
  return slice as Partial<ShellStoreState>;
}

export function createShellStore(opts: CreateShellStoreOptions): ShellStore {
  const { storageKey, version = DEFAULT_VERSION, migrate } = opts;
  const migrateFn = migrate ?? defaultMigrate;

  return createSsrSafePersistedStore<ShellStoreState>(
    (set, get) => ({
      // ── SsrSafeHydration ──────────────────────────────────────────────────────
      _hasHydrated: false,
      setHasHydrated: (v: boolean) => set({ _hasHydrated: v }),

      // ── State ──────────────────────────────────────────────────────────────────
      // Default supervisorOpen: 'chat' (B) — supervisor visible by default.
      // Only applies on fresh load; persisted preference is respected.
      supervisorOpen: "chat",
      // historyOpen always starts closed — NEVER persisted open (RN-5/RN-11).
      historyOpen: false,
      // null = default split — the layout resolves the concrete % (e.g. 30).
      splitPct: null,
      // Default closed; user's choice remembered between reloads. Independent slice.
      mobileDrawerOpen: false,

      // ── Supervisor open/close actions ───────────────────────────────────────────

      setSupervisorOpen: (open: SupervisorOpen) =>
        // RN-5 invariant: history can't be open while the supervisor is closed (state A).
        set(
          open === "closed"
            ? { supervisorOpen: "closed", historyOpen: false }
            : { supervisorOpen: open },
        ),

      // RN-6: reopening is chat-only — NEVER restores history.
      openSupervisor: () => set({ supervisorOpen: "chat" }),

      // RN-6: collapsing closes history too.
      collapseSupervisor: () => set({ supervisorOpen: "closed", historyOpen: false }),

      // ── History (additive) actions ──────────────────────────────────────────────

      setHistoryOpen: (open: boolean) => {
        if (!open) {
          set({ historyOpen: false });
          return;
        }
        // RN-5 invariant: history can't show while the supervisor is closed (state A).
        // setHistoryOpen is the literal field setter — it does NOT auto-open the
        // supervisor. The additive A → B+C intent lives in openHistory() (RN-7).
        if (get().supervisorOpen === "closed") {
          set({ historyOpen: false });
          return;
        }
        set({ historyOpen: true });
      },

      // RN-7 additive: opening history also opens the supervisor (A → B+C).
      openHistory: () => set({ supervisorOpen: "chat", historyOpen: true }),

      closeHistory: () => set({ historyOpen: false }),

      toggleHistory: () => {
        if (get().historyOpen) {
          set({ historyOpen: false });
        } else {
          // RN-7 additive: opening also opens the supervisor.
          set({ supervisorOpen: "chat", historyOpen: true });
        }
      },

      // ── splitPct ────────────────────────────────────────────────────────────────

      setSplitPct: (pct: number | null) => set({ splitPct: pct }),

      // ── Mobile (independent slice) ──────────────────────────────────────────────

      setMobileDrawerOpen: (open: boolean) => set({ mobileDrawerOpen: open }),
    }),
    {
      name: storageKey,
      version,
      migrate: (persisted, v) => migrateFn(persisted, v) as Partial<ShellStoreState>,
      // Only persist state fields — NOT setters, NOT _hasHydrated, NOT historyOpen (RN-5/11).
      partialize: (state): ShellPersistedState => ({
        supervisorOpen: state.supervisorOpen,
        splitPct: state.splitPct,
        mobileDrawerOpen: state.mobileDrawerOpen,
      }),
      // merge() runs on EVERY rehydrate (unlike migrate(), which Zustand skips when
      // stored version === store version). It is the only hook that sees corrupt
      // current-schema localStorage — so the SC-6 sanitization for the current
      // version lives here, not in migrate().
      merge: (persistedState, currentState): ShellStoreState => {
        const slice =
          persistedState !== null && typeof persistedState === "object"
            ? sanitizePersistedSlice(persistedState as Record<string, unknown>)
            : {
                supervisorOpen: "chat" as SupervisorOpen,
                splitPct: null,
                mobileDrawerOpen: false,
              };
        return {
          ...currentState,
          ...slice,
          // RN-5/RN-11: history is NEVER persisted open — always starts closed.
          historyOpen: false,
        };
      },
    },
  );
}
