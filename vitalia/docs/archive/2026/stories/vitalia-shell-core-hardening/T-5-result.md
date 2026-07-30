# T-5 Result — N3 → @luana/ui-kit: migrar staff+embudo a EntityWorkspaceLayout core

**Story:** vitalia-shell-core-hardening  
**Ticket:** T-5  
**Branch:** wip/vitalia  
**Date:** 2026-06-10  
**Commits:** d3b06b11 · 8d62c958 · a042e1df

---

## Deliverables completed

1. **StaffWorkspaceShell** (`vitalia/frontend/src/features/lisa/components/staff/workspace/StaffWorkspaceShell.tsx`)
   - Import changed from `@/components/shared/shell-organism/EntitySubNavBar` → `@luana/ui-kit`
   - Replaced manual `<div> + <EntitySubNavBar>` wrapper with `<EntityWorkspaceLayout>`
   - `isLoading` prop wired to doctor hydration state (skeleton when `isDoctorLoading && !initialDoctor`)
   - `activeLeaf` passed explicitly (vitalia uses static leaf segments `/perfil|/horarios|/servicios`)
   - `extractLeafFromPath()` retained as override-derivation helper

2. **LeadWorkspace** (`vitalia/frontend/src/features/adrian/components/embudo/lead/LeadWorkspace.tsx`)
   - Import changed from `@/components/shared/shell-organism/EntitySubNavBar` → `@luana/ui-kit`
   - Replaced `<EntitySubNavBar> + manual div` with `<EntityWorkspaceLayout>`
   - `isLoading` prop wired to `useLeadDetail` RQ state
   - `activeLeaf` prop retained (caller passes "resumen" | "historial")
   - Removed `WorkspaceSkeleton` sub-component (kit provides skeleton via `isLoading`)
   - `NotFoundState` sub-component kept for error/undefined data path

3. **NewLeadPage** (`vitalia/frontend/src/features/adrian/components/embudo/nuevo/NewLeadPage.tsx`)
   - Import changed from `@/components/shared/shell-organism/EntitySubNavBar` → `@luana/ui-kit`
   - Uses `EntitySubNavBar` directly (no leaf tabs on /nuevo form page, no layout wrapper needed)

4. **RETIRED brand-local EntitySubNavBar** — DELETED:
   - `vitalia/frontend/src/components/shared/shell-organism/EntitySubNavBar.tsx` (258 lines, 9.3K)
   - `vitalia/frontend/src/components/shared/shell-organism/EntitySubNavBar.test.tsx`

5. **Adaptar call-sites**: `resumen/page.tsx` + `historial/page.tsx` unchanged (they already pass `activeLeaf` prop to `LeadWorkspace`; `LeadWorkspaceProps.activeLeaf` retained for explicit override pattern)

6. **Kit additive-minimal edit** (permitted — missing N3 piece for static route segments):
   - Added `activeLeaf?: string | null` optional override prop to `EntityWorkspaceLayout`
   - When provided: overrides URL-derived `useParams<{leaf?}>()` (for static segments like `/perfil`)
   - When absent: existing URL-derivation behavior unchanged (backward-compatible)
   - 3 new tests in `core/@luana/ui-kit/src/__tests__/EntityWorkspaceLayout.test.tsx`

---

## Quality gates

| Gate | Result |
|---|---|
| `tsc --noEmit` vitalia/frontend | 0 errors |
| ESLint on changed files | 0 errors |
| Kit tests (EntityWorkspaceLayout) | 10/10 PASS |
| Targeted component tests (LeadWorkspace + NewLeadPage) | 8/8 PASS |
| `test-no-cross-brand-shell-mirror.test.ts` | 31/31 PASS |
| Other arch fitness (pre-existing failures) | 2 pre-existing FAIL unrelated to T-5 |

**Pre-existing arch test failures (not regressions from T-5):**
- `embudo/page.tsx` internal import of `@/features/adrian/api/embudo-server` — pre-existing violation
- `KNOWN_CROSS_FEATURE_INTERNAL_IMPORTS` stale entry for `src/features/inbox/hooks/use-conversation-filters.ts` — file deleted in T-4 inbox migration, allowlist not cleaned

---

## Acceptance checks

- [x] arch: staff+embudo importan `@luana/ui-kit` `EntityWorkspaceLayout`; brand-local retirado
- [x] cross-brand-shell-mirror allowlist: no change needed (EntitySubNavBar was brand-local vitalia only, not tracked in `KNOWN_SANCTIONED_SHELL_MIRROR` — simply DELETED)
- [x] SC-11: directorio→workspace→back pattern preserved via kit (EntityWorkspaceLayout renders the same N3 ribbon)
- [x] SC-12: leafs disabled sin entidad — handled by kit (EntitySubNavBar with `entity=null` renders master mode, all content leaves aria-disabled)
- [x] AC-10: embudo board/writes untouched — no changes to KanbanBoard, StageTransition, or board API layer

---

## Behavioral notes

- `StaffWorkspaceShell`: `extractLeafFromPath()` now used solely for the `activeLeaf` override (not activeLeaf derivation for rendering). Could be inlined, but kept for clarity + future reference.
- `LeadWorkspace`: loading state now shows kit's skeleton bar (replaces the custom `WorkspaceSkeleton` which was essentially the same thing)
- `NewLeadPage`: uses `EntitySubNavBar` directly (not `EntityWorkspaceLayout`) because the /nuevo form page has no leaf tabs — just a back link + entity identity header. This is correct usage.
