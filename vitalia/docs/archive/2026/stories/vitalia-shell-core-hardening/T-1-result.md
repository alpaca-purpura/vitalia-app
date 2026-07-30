# T-1-result — Refactor shell-store: máquina nueva (closed|chat + historyOpen) + migrate legacy

**State:** pushed · **Builder:** builder-frontend (sonnet) + finalize orchestrator (builder agotó contexto mid-verify; orchestrator corrió gates + commit — patrón continuation)

## Qué se construyó

- `vitalia/frontend/src/stores/shell-store.ts` — máquina nueva: `valeriaOpen: 'closed'|'chat'` + `historyOpen: boolean` (aditivo, push) vía `createSsrSafePersistedStore` (@luana/hooks, ADR-vitalia-006). `shellMode` ELIMINADO del estado runtime (RN-1) — sobrevive solo como key del `LegacyPersistedShape` que el migrate lee. `historyOpen` NO se persiste (RN-11/RN-5). Migrate legacy `{collapsed,rail,full,shellMode}` → estado nuevo válido + fallback con `console.warn` si corrupto (SC-18) + no-clobber SSR (setItem NO-OP pre-hydration).
- Componentes actualizados al contrato nuevo (mínimo para mantener verde — layout real va en T-2/T-3): `ShellOrganismLayoutClient`, `ValeriaSidebar`, `useViewportGuard`, `ShellModeToggle` (stub neutralizado — eliminación física en T-2), `ConversationModeButton` (inbox dejaba de compilar por `shellMode`).
- Tests: `shell-store.test.ts` + `shell-store-hydration.test.ts` (migración + no-clobber) + arch tests schema actualizados (`test-shell-store-schema*.test.ts`).

## Gates (G5 pre-commit smoke)

| Gate | Resultado |
|---|---|
| `npx tsc --noEmit` | ✅ 0 errors (tras `pnpm install` — dep `@tanstack/react-virtual` del ui-kit estaba declarada pero no instalada post harness-integrate; NO es deuda del ticket) |
| `npx vitest run` stores + shell-organism + arch | ✅ 40 files / 631 tests pass |
| `npx eslint` surfaces tocadas | ✅ clean |

## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Status |
|---|---|
| frontend-expert · vitalia-design-system | ✅ loaded (builder Step 0) |
| ADR-vitalia-006 (SSR-safe store) | ✅ loaded — factory consumida, no recreada |
| frontend-fsd · frontend-visual-fidelity · spanish-text · tdd-mandatory · tenant-isolation | ✅ loaded |
| design-system-canon.md | ✅ loaded (sin surface visual nueva en T-1) |

## Notas

- TDD: tests de la máquina nueva escritos RED primero (ver T-1-impl-log si el builder lo dejó); migrate + hydration cubiertos.
- `ShellModeToggle.tsx` queda como stub muerto a remover físicamente en T-2 (AC-1 grep=0 se cierra ahí).
