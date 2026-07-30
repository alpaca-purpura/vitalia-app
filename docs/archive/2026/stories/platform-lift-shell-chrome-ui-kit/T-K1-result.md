# T-K1 result — Kit scaffolding (organism/shell)

**Story:** `platform-lift-shell-chrome-ui-kit` · **Ticket:** T-K1 · **Brand:** platform
**State:** tests-passing (builder phase) · **Commits:** `a4758d51` (deliverables) + `5bce4823` (impl-log) · pushed `wip/vitalia` (`25289164..5bce4823`, fast-forward)

Executes accepted proposal `docs/promotion-protocol/proposals/2026-06-01-lift-shell-organism-to-core.md`. T-K1 = scaffolding only (factory + types + routing); visual components + RN-4 v4 fixes land in T-K2.

## Deliverables (5/5)

| # | Deliverable | File | Status |
|---|---|---|---|
| 1 | deps + SEMVER | `core/@luana/ui-kit/package.json` | `react-resizable-panels ^4.11.1` + `zustand ^5.0.5` added · 0.3.0→0.4.0 (minor) · lockfile +6 lines, 0 removed |
| 2 | generic types verbatim 03-arch | `core/@luana/ui-kit/src/organism/shell/types.ts` | ShellAgentDescriptor, ShellSubTabMeta, SupervisorOpen, ShellPersistedState, ShellStoreState, ShellChatStoreApi, ShellStore, ShellChatStore, CreateShellStoreOptions, ShellLayoutProps/Labels, ShellRoutingOptions. Zero brand tokens in logic. |
| 3 | store factory | `core/@luana/ui-kit/src/organism/shell/create-shell-store.ts` | `createShellStore({storageKey, version?, migrate?})` — CONSUMES `@luana/hooks/createSsrSafePersistedStore` (RN-8). Port of vitalia shell-store re-parametrized (RN-2: valeriaOpen→supervisorOpen, valeriaPct→splitPct). sanitize + no-clobber merge (SC-6) preserved. |
| 4 | routing helpers | `core/@luana/ui-kit/src/organism/shell/routing.ts` | extractAgentFromPath / extractSubtabFromPath / isValidAgent / isValidSubtab — catalog injected by argument, zero hardcoded brand slugs. |
| 5 | Vitest TDD (RED-first) | `core/@luana/ui-kit/src/organism/shell/__tests__/{create-shell-store,routing}.test.ts` | 15 store (machine A/B/C + migrate legacy + no-clobber hydration + generic-naming negative asserts) + 18 routing = 33 tests. |

## Gates

- **TDD RED→GREEN:** tests written first (RED confirmed: `Failed to resolve import "../routing"` / "../create-shell-store"), then implementations → **33/33 GREEN**.
- **tsc (organism/shell scope):** 0 errors. (116 pre-existing kit errors live only in files untouched by T-K1 — jest-dom matchers in EntityInfoCard/Picker/SubNavBar/label tests + `timezone-select.tsx` Intl.supportedValuesOf; confirmed via `git status` mine = CHANGELOG.md + package.json + new `src/organism/` only.)
- **Brand-token grep (logic):** `grep -riE '#01b2f8|vitalia|valeria|nicolify' src/organism` = 0 matches in executable code (verified by stripping all block+line comments → empty). Remaining grep hits are JSDoc provenance/usage examples ("port of vitalia", "brand passes 'vitalia-shell-state'") + test negative-assertions (`not.toHaveProperty("valeriaOpen")`) — acceptable per "0 en lógica".
- **eslint:** kit has no eslint config (gated by tsc + vitest; eslint runs on brand `frontend/src/`). Pre-commit hook passed on both commits.

## Machine fidelity (state machine A/B/C)

- A=closed: `setSupervisorOpen('closed')` + `collapseSupervisor()` force `historyOpen=false` (RN-5).
- B=chat: `openSupervisor()` never restores history (RN-6).
- C=chat+history: `openHistory()`/`toggleHistory()` force `supervisorOpen='chat'` + `historyOpen=true` (RN-7 additive).
- `splitPct: null` = default; mobile drawer = independent slice. `historyOpen` NEVER persisted open (no-clobber, SC-6) — `partialize` = {supervisorOpen, splitPct, mobileDrawerOpen}; `merge` forces historyOpen=false on every rehydrate.

## Decisión D (group-name collision)

T-K1 does NOT re-export react-resizable-panels' `Group`/`Panel`/`Separator` from the barrel (kit already exports a form `Group`). Public resize handle → `ShellResizeHandle` deferred to T-K2.

## Notes for downstream (auditor / T-K2)

- `ShellStore` typed as `SsrSafePersistedStore<ShellStoreState>` (the @luana/hooks interface), NOT zustand's `UseBoundStore` — the 03-arch `UseBoundStore` annotation was a loose placeholder; the factory's real return type carries `.persist`/`.getState`/`.setState` needed by the chat sub-tree. Added `ShellChatStore` alias for the brand-provided chat store.
- No barrel export wired yet from `src/index.ts` (T-K2 wires the public organism API once visual components exist) — T-K1 surfaces are consumed only by their own tests.
- The two new deps are symlinked into `core/@luana/ui-kit/node_modules/` (zustand@5.0.13, react-resizable-panels@4.11.1) after `pnpm install`.

## R30 — builder phase boundary

Builder output = `tests-passing`. No audit verdict claimed. Awaiting orchestrator → gate-runner → auditor-frontend (independent verdict).
