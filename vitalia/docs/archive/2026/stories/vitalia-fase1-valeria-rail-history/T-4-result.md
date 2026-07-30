# T-4 Result — ValeriaHistory molecule

**Story:** vitalia-fase1-valeria-rail-history (F1-S5)
**Ticket:** T-4
**State:** pushed
**Commit SHA:** a3494da1
**Branch:** wip/vitalia

## Files changed

| Action | Path |
|---|---|
| NEW | `vitalia/frontend/src/components/shared/shell-organism/ValeriaHistory.tsx` |
| NEW | `vitalia/frontend/src/components/shared/shell-organism/ValeriaHistory.test.tsx` |

## Skills consulted

| Skill | Reason | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite shell-organism molecule, runtime quality checklist | Server-First default; `"use client"` leaf only (state + events); no cross-feature imports |
| `tessl__react-patterns` | useMemo + useState pattern review | `useMemo` for filtered + grouped (expensive recompute on searchQuery change); `useState` for searchQuery + activeId |
| `tessl__shadcn-ui` | Input primitive selection | Reused existing `components/ui/input.tsx` (no recreate); Button ghost/icon size pattern |
| `tessl__tailwind` | Semantic token check | All tokens semantic: `border-border`, `text-foreground`, `text-muted-foreground`, `bg-muted`, `bg-agent-valeria-soft`. Zero hex. |
| `tessl__vitest` | Test patterns for user-event search + async RTL | `userEvent.setup()` + `await user.type()` + `user.keyboard("{Escape}")` patterns |

## Validators passed

| Gate | Status | Notes |
|---|---|---|
| `tsc --noEmit` | PASS | 0 errors |
| ESLint | PASS | 0 errors, 0 warnings (fixed unused `within` import + unused `user` variable) |
| Prettier | PASS | Auto-formatted both files |
| Vitest T-4 (18 tests) | PASS | 18/18 GREEN |
| Arch tests (64 tests) | PASS | 15 files / 64 tests — all green, no regressions |

## Test summary

```
ValeriaHistory — renders header + grouped items (SC-1 happy)
  ✓ renders header 'Conversaciones' + quick actions (Plus + PanelLeftClose)
  ✓ renders 8 mock items grouped Hoy(3)+Ayer(2)+Esta semana(3)
  ✓ group labels en Spanish neutro (Hoy / Ayer / Esta semana)

ValeriaHistory — search filter logic (SC-6 empty state)
  ✓ input search updates searchQuery on change
  ✓ filter case-insensitive (match 'reseñas' returns Hoy item 1)
  ✓ filter trim whitespace ('  reseñas  ' equals 'reseñas')
  ✓ empty state shows EmptyStateInline when 0 matches
  ✓ groups con 0 items NO renderizan label (Hoy/Ayer/Esta semana hidden)
  ✓ EmptyStateInline copy: 'Sin resultados' + 'Intenta con otra palabra'
  ✓ Press Escape en search con query → setSearchQuery('') NO colapsa Valeria

ValeriaHistory — i18n Spanish neutro (SC-9)
  ✓ search input placeholder 'Buscar conversación...'
  ✓ search input aria-label 'Buscar conversación'
  ✓ nav aria-label 'Historial conversaciones'

ValeriaHistory — HistoryItem active state (integration)
  ✓ click HistoryItem updates active state local
  ✓ active item has aria-current='true' + className includes 'bg-agent-valeria-soft'
  ✓ only one active item at a time
  ✓ onNewConversation callback dispatched al click Plus
  ✓ onCollapseToRail callback dispatched al click ChevronLeft
```

## Gherkin coverage

| Scenario | Tests | Status |
|---|---|---|
| SC-1 happy · history visible 8 items grouped 3+2+3 | 3 tests | PASS |
| SC-6 empty_state · búsqueda sin resultados | 7 tests | PASS |
| SC-9 i18n · header + labels + search placeholder | 3 tests | PASS |
| (integration) HistoryItem click + active state | 5 tests | PASS |

## Implementation notes

- `"use client"` justified: `useState` (searchQuery + activeId) + onChange + onKeyDown event handlers
- `useMemo` for `filtered` + `grouped` — avoids recompute on unrelated renders, appropriate for array filtering
- Escape key in search: `stopPropagation()` only when `searchQuery` is non-empty — prevents Valeria collapse while typing
- Default `activeId='1'` matches spec mockup (item 1 pre-selected)
- `HistoryGroup` renders `null` for 0-item groups (already implemented in T-3) — no additional logic needed
- Spanish neutro verified: 'Conversaciones', 'Nueva conversación', 'Colapsar a barra', 'Buscar conversación...', 'Buscar conversación', 'Historial conversaciones', 'Hoy', 'Ayer', 'Esta semana', 'Sin resultados', 'Intenta con otra palabra'

## Dependencies consumed

- T-2 (`_mock-conversations.ts`, commit d52292a0-era) — MOCK_CONVERSATIONS 8 items + MockConversation type
- T-3 (`HistoryGroup`, `HistoryItem`, `EmptyStateInline`, commit 046b2d44-era) — child components

## Chrome DevTools live verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (designed for WSL2+Windows bridge). Manual verification escalated to Chris staging gate. Component is ready for T-5 (ValeriaSidebar organism) to integrate.
