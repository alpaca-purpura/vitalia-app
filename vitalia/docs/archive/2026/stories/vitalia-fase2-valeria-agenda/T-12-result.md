# T-12 Result — FE API Hooks + Zustand + Page Server Component + ValeriaAgendaView Root

**Story:** vitalia-fase2-valeria-agenda  
**Ticket:** T-12  
**Fecha:** 2026-05-26  
**Estado:** tests-passing

---

## IMPL-LOG

### Skills Consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `frontend-expert` | ALWAYS — FSD-Lite, ESLint, coverage baseline, arch tests | FSD-Lite paths, no default exports, "use client" on leaf components |
| `tessl__react-patterns` | ALWAYS — error boundaries, loading/error/empty, ARIA, stable keys | Loading/empty/error states en ValeriaAgendaView; aria-live="polite" en freshness; aria-label en main |
| `tessl__shadcn-ui` | ALWAYS — reuse Shadcn Button from components/ui/ | Button component reused in AgendaHeader view toggle |
| `tessl__tailwind` | ALWAYS — utility-first, cn() | cn() para conditional classes; no inline style |
| `tessl__zod` | Stores + hooks use Zod-defined types | Types come from T-11 agenda-schema.ts; stores use those types |
| `tessl__nextjs-app-router-modularization` | page.tsx + ValeriaAgendaView mix server/client | Strict split: page.tsx = pure Server Component, ValeriaAgendaView = "use client" root |
| `tessl__graceful-degradation` | SSR fetch + polling | agenda-server.ts: try/catch returns emptyGrid; React Query retry built-in |

### Architecture Decisions

1. **ValeriaAgendaView as root client boundary** — `"use client"` on first line per arch test FE-A5. Hydrates React Query cache with SSR `initialData` via `queryClient.setQueryData()` on mount.

2. **agendaKeys factory** — Stable tuple keys `["agenda", "grid", tenantId, view, date, filter]` enable targeted `invalidateQueries` via `agendaKeys.all(tenantId)` prefix matching.

3. **Polling 30s** — `refetchInterval: 30_000` with `staleTime: 25_000` to avoid redundant refetch when data is fresh.

4. **Zustand partialize for localStorage** — Only `drawerWidth` + `lastView` persisted. Session state (selectedSlotId, drawerOpen, activePreset) is ephemeral (URL is SSoT for filters).

5. **MSW not installed** — Tests use `vi.fn()` mocking of `vitaliaFetch`. MSW handlers provided as `createAgendaMockFetch()` factory in `src/test-utils/msw/handlers/agenda-handlers.ts` for future MSW integration.

6. **agenda-server.ts exported from barrel** — page.tsx must import from `@/features/valeria` (FE-A4 arch test enforces no internal path imports). `getInitialAgendaState` added to index.ts.

7. **biome-ignore comments** — Used instead of `eslint-disable-next-line react-hooks/exhaustive-deps` since react-hooks ESLint plugin is not configured in vitalia frontend eslint.config.mjs.

---

## Deliverables Created

| File | Type | Notes |
|---|---|---|
| `features/valeria/api/agenda.ts` | React Query v5 hooks | agendaKeys + 8 hooks + polling 30s |
| `features/valeria/api/agenda-server.ts` | SSR fetch | getInitialAgendaState, graceful degradation |
| `features/valeria/api/payments.ts` | Mutation hook | useChargeMutation + X-Idempotency-Key |
| `features/valeria/api/fiscal.ts` | Mutation hook | useFiscalEmitMutation |
| `features/valeria/api/notify.ts` | Mutation hook | useSendNotificationMutation |
| `features/valeria/store/agenda-store.ts` | Zustand | drawerWidth persisted to vitalia.agenda.drawerWidth |
| `features/valeria/store/agenda-filters-store.ts` | Zustand | lastView persisted to vitalia.agenda.lastView |
| `features/valeria/hooks/useAgendaFilters.ts` | Hook | URL params + Zustand sync |
| `features/valeria/hooks/useDrawerWidth.ts` | Hook | drawerStyle CSS object |
| `features/valeria/hooks/useFreshness.ts` | Hook | 30s interval + formatRelativeTime |
| `app/[tenantId]/(shell-organism)/valeria/agenda/page.tsx` | Server Component | SSR + metadata |
| `features/valeria/components/agenda/ValeriaAgendaView.tsx` | Client root | Hydration + polling + telemetry |
| `features/valeria/components/agenda/AgendaHeader.tsx` | Client component | View toggle + date nav + freshness |
| `features/valeria/api/agenda.test.ts` | Tests | 13 tests — agendaKeys + hooks |
| `features/valeria/store/agenda-store.test.ts` | Tests | 14 tests — drawer store |
| `features/valeria/store/agenda-filters-store.test.ts` | Tests | 9 tests — filters store |
| `features/valeria/components/agenda/ValeriaAgendaView.test.tsx` | Tests | 7 tests — component render |
| `features/valeria/components/agenda/AgendaHeader.test.tsx` | Tests | 9 tests — toolbar |
| `test-utils/msw/handlers/agenda-handlers.ts` | Test utils | createAgendaMockFetch factory (SC-4, SC-5) |
| `features/valeria/index.ts` | Modified | +ValeriaAgendaView, stores, hooks, getInitialAgendaState |
| `vitest.config.ts` | Modified | +store + hooks coverage include paths |

---

## Quality Gates

| Gate | Status | Notes |
|---|---|---|
| tsc --noEmit | PASS | 0 errors, strict mode |
| ESLint | PASS | 0 errors, 0 new warnings |
| Vitest (172 files, 1798 tests) | PASS | All green |
| FE-A4 no-cross-feature-imports | PASS | page.tsx imports from @/features/valeria barrel |
| FE-A5 use client directive | PASS | All hook-using files have "use client" as first line |
| Coverage threshold 20% | PASS | Store + hooks included in coverage |

---

## Acceptance Criteria

| AC | Status |
|---|---|
| A1: Page SSR — ValeriaAgendaPage async params + getInitialAgendaState | PASS |
| A2: useAgendaGrid + 30s polling + placeholderData | PASS |
| A3: useChargeMutation invalidates grid + appointment detail keys | PASS |
| A4: Mock fetch handlers (SC-4 403, SC-5 409) | PASS |
| A5: Zustand drawer + filters stores with localStorage persist | PASS |

---

## Live Verification

`chrome-devtools-verify` skill is marked DEPRECATED (Linux Mint, WSL2 bridge required). Manual verification escalated to Chris staging gate per implementation-flow step.

---

## Downstream

T-12 blocks: T-13 (AgendaPresetFilters + AgendaCalendar + CrearCitaButton) and T-14 (AppointmentDrawer). Both will consume `useDrawerStore`, `useAgendaGrid`, and `useAgendaFilters` from this ticket.
