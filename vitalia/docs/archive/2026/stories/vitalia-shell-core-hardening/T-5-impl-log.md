# T-5 Impl Log — N3 → @luana/ui-kit: migrar staff+embudo a EntityWorkspaceLayout core

**Ticket:** T-5 — vitalia-shell-core-hardening
**Branch:** wip/vitalia
**Date:** 2026-06-10

---

## Plan

### Design-system-first (D1)
- Reuse `EntityWorkspaceLayout` + `EntitySubNavBar` + `EntitySubNavLeaf` + `EntitySubNavEntity` from `@luana/ui-kit`
- No new atoms invented; brand-local `EntitySubNavBar.tsx` (mirror) gets RETIRED

### Mockup scope
- SC-11: directorio→workspace→back staff Y embudo mismo patrón ✓
- SC-12: leafs disabled sin entidad (aria-disabled + roving tabindex) ✓ (handled by kit)
- AC-10: embudo board/writes live-verified intactos (not touched in this ticket)

### Test battery
- Adapt `EntitySubNavBar.test.tsx` (brand-local) to test the brand-local mirror deletion (becomes a DELETE)
- New import-from-kit smoke tests for StaffWorkspaceShell + LeadWorkspace
- Architecture fitness: `test-no-cross-brand-shell-mirror.test.ts` passes (no allowlist change needed)

### Integration (CONN)
- `StaffWorkspaceShell` imported by `[doctor-id]/layout.tsx` — remains unchanged
- `LeadWorkspace` imported by `resumen/page.tsx` + `historial/page.tsx` — minor call-site change (remove `activeLeaf` prop)
- No route or nav changes

---

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite patterns, boundary matrix, test conventions | Apply; kit import = `@luana/ui-kit`, workspace-linked |
| React patterns baseline | Error boundaries, loading/error/empty states, aria | Kit provides aria; `isLoading` prop for skeleton |
| Next.js App Router Server/Client split | layout.tsx = Server, Shell = Client | Preserved — no change to layout.tsx |
| Shadcn UI conventions | Kit uses Skeleton from `./skeleton` | Re-export from kit is fine |
| `vitalia-design-system` | Canon §2.1-2.2: EntityWorkspaceLayout is the canon | Confirmed |

---

## Key Finding: Routing Pattern Mismatch (Additive-Minimal Kit Edit Required)

`EntityWorkspaceLayout` derives `activeLeaf` via `useParams<{ leaf?: string }>()`, assuming a dynamic `[leaf]` route segment.

Vitalia routes use STATIC leaf segments:
- Staff: `/{tenantId}/lisa/staff/{doctor-id}/perfil` → `useParams()` has no `leaf` key → `activeLeaf = null` → N3 tabs show no active state (BROKEN)
- Embudo: `/{tenantId}/adrian/embudo/{leadId}/resumen` → same issue

**Additive-minimal kit edit (PERMITTED per ticket rule):**  
Add optional `activeLeaf?: string | null` prop to `EntityWorkspaceLayout` that overrides URL-derived value. This is:
- Additive (new optional prop, backward-compatible)
- Minimal (1 prop, 1 line change in component body)
- Required (vitalia N3 uses static segments; the kit assumed dynamic `[leaf]`)

PAUSE-POINT check: this is NOT a non-additive edit (not removing/changing existing behavior). The kit still derives from `useParams` when the override is not provided. Proceeding.

---

## Commit Plan (3 incremental commits by pathspec)

1. **kit-patch**: `core/@luana/ui-kit/src/EntityWorkspaceLayout.tsx` — add optional `activeLeaf` override prop + update test
2. **staff-migrate**: `vitalia/frontend/src/features/lisa/components/staff/workspace/StaffWorkspaceShell.tsx` — import from `@luana/ui-kit`, use `EntityWorkspaceLayout`
3. **embudo-migrate + retire**: `vitalia/frontend/src/features/adrian/components/embudo/lead/LeadWorkspace.tsx` + call-sites (`resumen/page.tsx` + `historial/page.tsx`) + DELETE brand-local `EntitySubNavBar.tsx` + `EntitySubNavBar.test.tsx`

---

## Mockup Scope Notes

Ticket scopes only the N3 migration + retire. Not building new UI. No visual change expected (same layout, different import source).
