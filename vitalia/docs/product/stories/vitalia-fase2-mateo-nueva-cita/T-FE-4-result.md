# T-FE-4 Result — FE Integration + E2E + Live Verify

**Ticket:** T-FE-4 — FE · FormActionBar + integración + E2E live-verify
**Story:** vitalia-fase2-mateo-nueva-cita
**Date:** 2026-06-22
**Builder:** builder-frontend (claude-sonnet-4-6)

---

## Status

`tests-passing` — tsc CLEAN · ESLint 0 errors · Vitest 2659/2659 passed (292 files)
Live-verify: BE contract verified (schema 422→403 path), E2E runner pre-existing systemic issue (see notes)

---

## Deliverables shipped

### New files
- `vitalia/frontend/src/features/mateo/components/nueva-cita/NuevaCitaActions.tsx`
  - Thin wrapper around `@luana/ui-kit` `FormActionBar` with `accent="mateo"`, `submitLabel="Crear cita"`, `testId="nueva-cita-actions"`.
  - Props: `{ onCancel, onSubmit, submitting?, submitDisabled?, hint? }`.
- `vitalia/frontend/e2e/specs/smoke/nueva-cita.smoke.spec.ts`
  - SC-happy (route renders, form sections visible, submit disabled initially) + SC-a11y (axe wcag2aa).
  - All API mocked via `page.route()`. Uses `assertShellMounted(page)` before axe (HB-68).
- `vitalia/frontend/e2e/specs/regression/mateo/nueva-cita.spec.ts`
  - Full regression matrix: SC-happy, SC-crear-paciente, SC-solape, SC-reasignar, SC-mini-vista, SC-cancelled-reuse, SC-a11y, SC-i18n-tz, SC-race.

### Modified files
- `vitalia/frontend/src/features/mateo/components/nueva-cita/NuevaCitaView.tsx`
  - Replaced all placeholder inputs with real T-FE-2 pickers (ServicePicker, DoctorPicker, PatientPickerWithCreate, CanalPicker).
  - Wired T-FE-3 availability (AvailabilityChip, DayAvailabilityStrip, FreeDoctorsList).
  - `availabilityStatus` sourced from Zustand store (set by AvailabilityChip internally — RN-10 fail-closed: null=block).
  - `isAvailabilityBlocked = availabilityStatus !== "available"`.
  - Integrated NuevaCitaActions as sticky footer.
  - `data-testid="nueva-cita-form"` on form element.
- `vitalia/frontend/src/features/mateo/components/nueva-cita/__tests__/NuevaCitaView.test.tsx`
  - Added `vi.mock("../../../hooks/use-patients", ...)` — fixes "No QueryClient set" from PatientPickerWithCreate.
  - Added `vi.mock("../../../hooks/use-availability", ...)` — fixes "No QueryClient set" from DayAvailabilityStrip.
  - Updated FormActionBar mock to pass-through `testId` prop (supports both `"form-action-bar"` and `"nueva-cita-actions"`).
  - Added 5 new T-FE-4 integration assertions (NuevaCitaActions renders, submit disabled, CanalPicker, PatientPicker, FreeDoctorsList no-slot, DayAvailabilityStrip hidden when no startTime).
  - Total: 11 tests passing (up from 6 with all green).
- `vitalia/frontend/src/features/mateo/hooks/use-nueva-cita.ts`
  - Fixed BE path: `/api/v1/offers/servicios` → `/api/v1/offer/servicios` (singular — BE contract verified).
- `vitalia/frontend/src/features/mateo/index.ts`
  - Barrel exports for NuevaCitaActions + NuevaCitaActionsProps.

---

## Quality gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS — 0 errors |
| `eslint src/` | PASS — 0 errors |
| `vitest run` | PASS — 2659/2659 tests (292 files) |
| Architecture fitness | PASS — included in vitest run |
| E2E smoke | SEE NOTES — pre-existing systemic issue |
| Live-verify (Rule #37) | PARTIAL — BE schema validated, E2E runner broken |

---

## BE contract verification (anti-embudo)

Endpoints verified against live BE at `http://localhost:8002`:

| Hook | FE path (fixed) | BE path (OpenAPI) | Status |
|---|---|---|---|
| `useNuevaCitaServices` | `/api/v1/offer/servicios` | `/api/v1/offer/servicios` | MATCH |
| `useNuevaCitaFreeDoctors` | `/api/v1/scheduling/availability/free-doctors` | `/api/v1/scheduling/availability/free-doctors` | MATCH |
| `useAvailabilityCheck` | `/api/v1/scheduling/availability/check` | `/api/v1/scheduling/availability/check` | MATCH |
| `useDayStrip` | `/api/v1/scheduling/availability/day-strip` | `/api/v1/scheduling/availability/day-strip` | MATCH |
| `useNuevaCitaCreate` | `/api/v1/scheduling/appointments` | `/api/v1/scheduling/appointments` | MATCH |
| `useSearchPatients` | `/api/v1/crm/patients?q=...` | `/api/v1/crm/patients` | MATCH |

Serializer `serializeCreateAppointment` maps camelCase→snake_case matching BE `CreateAppointmentRequestDTO`.

POST /api/v1/scheduling/appointments with correct body → 422 (missing auth headers) → 403 (RBAC with fake IDs) confirms schema accepted.

---

## E2E runner issue (pre-existing, not introduced by T-FE-4)

**Symptom:** `npx playwright test --project=smoke` throws `"Playwright Test did not expect test.describe.configure() to be called here"`.

**Root cause:** Pre-existing. `clerk.setup.ts` line 31 `setup.describe.configure({ mode: "serial" })` conflicts with project collection in current Playwright version. Affects ALL smoke specs (verified by running `inbox.smoke.spec.ts` — same error).

**Evidence:** `git stash` + re-run shows same error before T-FE-4 changes.

**Impact:** E2E specs written and verified for correctness (correct API mock paths, HB-68 `assertShellMounted`, proper `base.ts` imports). Cannot run them native until the pre-existing Playwright setup issue is resolved.

**Action required:** `/pm-vitalia` log as HB issue for Playwright project dependency resolution fix.

---

## Live verify evidence

```yaml
dod_live_verified: false  # E2E runner pre-existing broken; writes not exercised live
dod_env: "BE localhost:8002 up · FE localhost:3002 up (307 auth redirect = correct)"
dod_evidence:
  - action: "GET /api/v1/offer/servicios → 200 (with auth token)"
    observed: "Services endpoint returns correctly"
    backend_log: "BE logs show GET 200 (no 500)"
  - action: "POST /api/v1/scheduling/appointments with correct snake_case payload → 422 then 403"
    observed: "422=missing headers (not body), 403=RBAC (fake IDs) — schema accepted, serializer correct"
    backend_log: "POST /api/v1/scheduling/appointments HTTP/1.1 422 / 403"
  - action: "Route /e69a691d.../mateo/agenda/nueva-cita → 307"
    observed: "Correct auth redirect (not 404 — route registered)"
    backend_log: "n/a (FE route)"
notes: "Full live write (create cita 201, inline patient, force overlap 409) pending — requires Playwright E2E runner fix OR Chrome DevTools MCP session. Escalated to Chris for G-phase live verification."
verified_at: 2026-06-22
```

---

## Skills consulted

| Skill | Reason | Decision |
|---|---|---|
| frontend-expert | FSD boundaries, React patterns, QueryClient in tests | Added `vi.mock()` for child hooks; used stub pattern |
| playwright-expert | E2E structure, assertShellMounted HB-68, base.ts import | Applied per-spec; confirmed pre-existing E2E runner issue |
| chrome-devtools-verify | Live verify gate Rule #37 | Runner unavailable this session; BE contract verified manually |

---

## Notes for G-phase (Chris verify)

Rule #37 requires live writes. The following need verification in dev-app:
1. Select service → doctor → patient (typeahead) → set date/time → Crear cita → 201 + agenda grid reflects
2. Select existing patient with duplicate → dedup toast (SC-crear-paciente)
3. Force time overlap (same doctor, same slot) → 409 conflict label shown in chip
4. Patiente inline create: type name not in list → "Crear {q}" → POST /crm/patients → 201

These require the Clerk auth token + real clinic seed data. Run from `dev-app.vitalialat.com` or `localhost:3002` with `dr.demo@vitalialat.com` / `DrDemo2026!`.
