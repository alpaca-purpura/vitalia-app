# T-G2F13-fe — FE result

**Ticket:** G2-F13-FE (bugfix — specialist UUID shown instead of name)
**Story:** vitalia-fase2-lisa-servicios
**Commit:** 8a51ad4b
**Branch:** wip/vitalia

## Skills consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary, API standards, runtime quality checklist | useServicioDetail clinic header wiring; no mock anti-patterns in tests |
| `brand-expert` | N/A (no brand-studio surface touched) | — |

## Changes

### `servicios.types.ts`
- `SpecialistLink` interface: added `display_name?: string | null` and `specialty?: string | null` (additive, backwards-compatible). The existing comment about "NO display_name on the wire" was stale — updated to reflect G2-F13 BE enrichment.

### `servicios.ts — useServicioDetail`
- Added `const clinicId = useClinicId()` (already imported via `useClinicId` used in mutations).
- Passed `clinicId` to `fetchClient` options so the detail GET sends `X-Clinic-ID`. The BE uses this header to resolve `display_name + specialty` via the clinic roster join. Degrades gracefully when `clinicId` is null (BE returns `display_name: null`).

### `EspecialistasView.tsx`
- For each specialist in the list, computes:
  - `name = s.display_name ?? null`
  - `initials` from first 2 words of `name` (e.g. "Dra. María López" → "DM"); fallback `"E"` when no name
  - `shortId = s.doctor_id.slice(0, 8)` for the fallback secondary line
- Renders `name ?? "Especialista"` as `font-medium` primary line
- Renders `s.specialty ?? shortId` as `text-muted-foreground` secondary line
- UUID (`doctor_id`) never shown as primary/raw identifier

### `EspecialistasView.test.tsx`
4 new G2-F13 regression tests added:
- `[G2-F13] renders display_name and specialty when BE enriches the DTO` — asserts name + specialty visible, UUID NOT visible
- `[G2-F13] renders initials from display_name in AvatarFallback`
- `[G2-F13] fallback to 'Especialista' + short id when display_name is null`
- `[G2-F13] multiple specialists: each renders its own name or fallback`

Existing tests updated: removed `"Doctor ID: doc-uuid-X"` assertions (those patterns no longer render); added `display_name + specialty` to specialist fixtures.

## Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS (0 errors) |
| `eslint` scoped to 4 touched files | PASS (0 errors) |
| `vitest run EspecialistasView.test.tsx` | PASS (9/9) |
| `vitest run servicios/` | PASS (161/161, 0 regressions) |

## Scope notes

ONLY touched the 3 FE files + 1 test file as specified. BE files (`dtos.py`, `servicios_router.py`, `specialist_link_service.py`, `test_specialist_link_service.py`) left untouched — those belong to the parallel builder-backend session.
