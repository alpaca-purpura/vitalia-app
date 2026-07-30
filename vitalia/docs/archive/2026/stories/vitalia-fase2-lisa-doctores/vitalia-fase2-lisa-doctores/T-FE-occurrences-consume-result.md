# T-FE-occurrences-consume — Result

**Story:** vitalia-fase2-lisa-doctores  
**Ticket:** T-FE-occurrences-consume (D3-C fix)  
**State:** tests-passing (awaiting gate-runner + auditor-frontend)  
**Date:** 2026-06-12

---

## Summary

Fixed the D3-C infinite paint bug: `recurrentBlockVisibleInWeek()` only checked `endConditionKind === "end_date"`, ignoring `occurrences` / `open_ended` → infinite paint. Fix: replaced client-side recurrence expansion with BE occurrence projection SSoT.

---

## Deliverables Shipped

### 1. `useAvailabilityOccurrences` hook

- File: `vitalia/frontend/src/features/lisa/api/staff.ts`
- Query key: `staffKeys.occurrences(doctorId, fromIso, toIso)` → `["lisa","staff","detail",id,"occurrences",from,to]`
- Endpoint: `GET /{doctor_id}/availability-occurrences?from=&to=`
- Actor headers: includes `X-User-ID` (required by BE for actor-header consistency)
- Enabled gate: `isLoaded && !!isSignedIn && !!doctorId && !!fromIso && !!toIso`
- Response unwrap: `res.occurrences ?? []`
- Exported from barrel `index.ts`

### 2. `AvailabilityCalendar.tsx` refactor

- File: `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/AvailabilityCalendar.tsx`
- **DELETED functions:** `recurrentBlockVisibleInWeek`, `oneOffBlockVisibleInWeek`, `blockDayOfWeek`, `blocksByDay` client expansion
- **PAINT source:** `useAvailabilityOccurrences` per week window
- **EDIT source:** `useAvailabilityBlocks` kept ONLY for BloquePopover lookup
- `CalendarBlock` component now accepts `AvailabilityOccurrence` (not `AvailabilityBlock`)
- Occurrence click resolves `blockId` → full `AvailabilityBlock` via `blocksMap` for popover
- Stable key: `${occ.blockId}-${occ.occurrenceDate}` (not array index)
- `occurrencesByDay`: computed via `useMemo` from occurrences + `occurrenceDayOfWeek()`
- DnD drag-create logic preserved unchanged

### 3. `AvailabilityOccurrence` type

- File: `vitalia/frontend/src/features/lisa/types/staff.types.ts`
- Fields: `blockId, occurrenceDate, startTime, endTime, kind, freq, patternSummary`
- camelCase mirrors BE `AvailabilityOccurrenceDTO` (alias_generator=to_camel)
- Exported from barrel

### 4. Tests

**Vitest (RED→GREEN):**
- `vitalia/frontend/src/features/lisa/api/__tests__/staff-occurrences-api.test.ts` — 12 tests
  - `staffKeys.occurrences` key factory
  - `AvailabilityOccurrence` type shape
  - SC-D3C-1: weekly×2 → exactly 2 occurrences; week 3 = 0 (regression)
  - SC-D3C-6: two overlapping blocks → both visible
  - SC-D3C-7: delete → occurrences key stable for invalidation

**Updated mock** in `horarios.test.tsx` — added `useAvailabilityOccurrences` mock alongside existing mocks.

**E2E regression:**
- `vitalia/frontend/e2e/regression/vitalia-fase2-lisa-doctores/horarios-occurrences-d3c.spec.ts`
- 3 specs: SC-D3C-1, SC-D3C-6, SC-D3C-7
- All 3 PASS (week-agnostic call-count strategy for SC-D3C-1)
- Listed under `[smoke]` project per playwright.config.ts

---

## V-D3C-NODUP

```bash
grep -r "recurrentBlockVisibleInWeek\|oneOffBlockVisibleInWeek\|blockDayOfWeek" vitalia/frontend/src/
```
Results: **0 live function definitions** (only in comments documenting the deletion).

---

## G5 Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS (0 errors) |
| `eslint src/features/lisa` | PASS (0 errors, 0 warnings added) |
| `vitest run src/features/lisa` | PASS (415 tests, 37 files) |
| E2E SC-D3C regression | PASS (3/3 in [smoke] project) |
| V-D3C-NODUP grep | PASS (0 live matches) |

---

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `frontend-expert` (React patterns baseline) | Always-on for FE tickets | Server-first default; `"use client"` only where needed; stable keys (blockId+date not index); `useMemo` for occurrencesByDay; error boundary on route component |
| `frontend-fsd.md` | FSD-Lite boundary matrix | No cross-feature imports; hook stays in `features/lisa/api/`; type in `types/`; exported via barrel `index.ts` |
| `master-data.md` | Date display in calendar | `Intl.DateTimeFormat("es-419")` — NEVER `toLocaleDateString()` (already enforced, preserved) |
| `spanish-text.md` | User-facing strings | Tuteo verified: "Semanal", "Quincenal", "Cada semana", "bloque" — no voseo |
| `tdd-mandatory.md` | TDD RED→GREEN | RED tests written FIRST (`staffKeys.occurrences` not a function → 4 failures), then implementation |
| `tenant-isolation.md` | HIPAA-lite dual filter | `fetchClient` auto-injects X-Tenant-ID; explicit clinicId passed; X-User-ID via `useStaffActorHeaders()` |

---

## Live Verify Evidence

**Environment:** `http://localhost:8002` (backend) + `http://localhost:3002` (frontend dev)  
**Tenant:** `e69a691d-070e-5caf-a053-6e74642ec100`  
**User:** dr.demo@vitalialat.com (`527050c3-1b2b-5e4f-b85d-394bbd0b796d`)  
**Doctor:** Carlos (`2464fad7-2124-46a0-9b41-cef9e489cc8d`, clinic `f035be5b-0ac4-5210-8fc3-395650ca2b83`)

**Action:** `POST /api/v1/vitalia/clinics/doctors/{id}/availability-blocks` — created weekly block, occurrences=2, day_of_week=0 (Monday), 09:00–11:00. Block ID: `01d05665-498c-4110-bcb5-f2d067e4f378`. Created: `2026-06-12T05:52:19Z` (Thursday → first occurrence = Monday June 15).

**Observed occurrences per week (via GET availability-occurrences):**

| Week | from | to | Occurrences | Expected |
|---|---|---|---|---|
| Current (week 1) | 2026-06-08 | 2026-06-14 | 0 | 0 (block created Jun 12, first Monday = Jun 15) |
| Week 2 | 2026-06-15 | 2026-06-21 | 1 (Jun 15) | 1 |
| Week 3 | 2026-06-22 | 2026-06-28 | 1 (Jun 22) | 1 |
| Week 4 | 2026-06-29 | 2026-07-05 | **0** | 0 (occurrences=2 exhausted) |

**D3-C fix confirmed:** Week 4+ returns 0 occurrences. Before fix, `recurrentBlockVisibleInWeek()` would return `true` for ALL weeks → infinite paint.

**Backend log:** `GET /api/v1/vitalia/clinics/doctors/*/availability-occurrences 200` for all queries.  
**Console errors:** 0  
**Test block cleanup:** `{"deleted":true,"preserved_appointments":0}` ✓

---

## Files Changed

| File | Change |
|---|---|
| `vitalia/frontend/src/features/lisa/api/staff.ts` | Added `staffKeys.occurrences`, `useAvailabilityOccurrences` hook |
| `vitalia/frontend/src/features/lisa/types/staff.types.ts` | Added `AvailabilityOccurrence` interface |
| `vitalia/frontend/src/features/lisa/index.ts` | Exported `useAvailabilityOccurrences`, `AvailabilityOccurrence` |
| `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/AvailabilityCalendar.tsx` | D3-C fix: deleted 3 buggy functions + client expansion; added BE occurrence paint |
| `vitalia/frontend/src/features/lisa/components/staff/__tests__/horarios.test.tsx` | Added `useAvailabilityOccurrences` mock |
| `vitalia/frontend/src/features/lisa/api/__tests__/staff-occurrences-api.test.ts` | NEW — 12 RED→GREEN tests |
| `vitalia/frontend/e2e/regression/vitalia-fase2-lisa-doctores/horarios-occurrences-d3c.spec.ts` | NEW — 3 regression e2e specs |
