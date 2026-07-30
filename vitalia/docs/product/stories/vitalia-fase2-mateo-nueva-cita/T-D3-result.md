# T-D3 Result — strip disponibilidad multi-doctor día-driven + filtro hora

**SHA:** `82731018`
**Branch:** `wip/vitalia`
**Push:** `97a08d11..82731018`

## Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS (0 errors) |
| `eslint src/features/mateo` | PASS (0 errors, 0 warnings) |
| `vitest run src/features/mateo` | PASS (425/425) |

## Diff summary (12 files, +1123 -335)

### New files (3)
- `utils/availability-filter.ts` — `isDoctorFreeAt(blocks, timeHHMM, tz)` + `filterFreeDoctors()`. Half-open `[start,end)` semantics (RN-2). Advisory client-side only (RN-10).
- `utils/__tests__/availability-filter.test.ts` — 10 unit tests: half-open, back-to-back (RN-2), empty blocks, invalid input.
- `hooks/__tests__/use-service-day.contract.test.ts` — contract test: endpoint URL/params + BE snake_case→FE camelCase normalization + fail-closed + empty doctors[].

### Modified files (9)
- `types/agenda-schema.ts` — added `DayBlockItem` type export, `ServiceDayDoctorSchema`, `ServiceDayResponseSchema` (reusing `DayBlockItemSchema`).
- `hooks/use-availability.ts` — added `availabilityKeys.serviceDay`, `normalizeServiceDay()`, `useServiceDayStrips({tenantId, serviceId, dateLocal})`. Fail-closed (disabled when null). `queryKey` includes `dateLocal` → auto-refetch on day-change.
- `DayAvailabilityStrip.tsx` — **complete rewrite** 1→N swimlane per doctor. Props: `doctors[]`, `isPending`, `isError`, `selectedDoctorId`, `onSelectDoctor`. SwimLane: label `w-24` + timeline bar `flex-1`; working=`bg-success/25`, busy=`bg-destructive/50`, selected=`--agent-mateo` amber; time-cursor on hora set; `sin-horario` (RN-4); keyboard Enter/Space.
- `DayAvailabilityStrip.test.tsx` — rewritten for new API (N lanes, empty/sin-horario, time-cursor, selected-slot, keyboard).
- `FreeDoctorsList.tsx` — **re-role**: props now `doctors: ServiceDayDoctor[], startHourStr, timezone`. No hora → hint. With hora → `filterFreeDoctors()` advisory filter. 1-click → `setSelectedDoctorId`.
- `FreeDoctorsList.test.tsx` — rewritten for new re-role props.
- `NuevaCitaView.tsx` — wired `useServiceDayStrips`, updated `DayAvailabilityStrip` (new props, visibility: `selectedServiceId && startDateStr`), updated `FreeDoctorsList` (new props). Intro block visibility: `!startDateStr`. T-D2 controls untouched.
- `NuevaCitaView.test.tsx` — added `useServiceDayStrips` to use-availability mock; updated `M1`/`T-D2` tests for new intro condition.
- `e2e/regression/mateo/nueva-cita.spec.ts` — added `SERVICE_DAY_MOCK`, `SERVICE_DAY_EMPTY`; updated `setupHappyMocks` to include service-day route; updated `SC-mini-vista`; added `SC-D3-strip` group (3 scenarios).

## Constraints satisfied

- ✅ DO NOT TOUCH: Fecha/Hora controls (T-D2) — untouched
- ✅ DO NOT TOUCH: core/ (forbidden), other brands, BE (T-D1 done)
- ✅ Fail-closed: hook disabled when `serviceId` null or `dateLocal` empty
- ✅ Advisory filter: `isDoctorFreeAt` client-side; server `availability/check` is authority (RN-10)
- ✅ Half-open `[start,end)`: back-to-back free (RN-2) — tested
- ✅ PHI-safe: `doctor_label` = professional name only, no patient PHI
- ✅ Spanish neutro: "Pon una hora", "No hay médicos disponibles a las…", "Sin horario"
- ✅ Named exports only (no default exports)
- ✅ `// cap: scheduling.mateo-agenda` header on all new files

## Bidirectional validator

SOFT_DRIFT (advisory): `vitalia/_bidirectional-validation.json` G10 1 drift — pre-existing, not introduced by T-D3.

## Skills consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundaries, RQ patterns, form-runtime array defaults | Single data source in parent (`NuevaCitaView`); no default exports; `"use client"` in SwimLane components |
| `vitalia-design-system` | Token usage for swimlane colors (agent-mateo, success, destructive) | Used `hsl(var(--agent-mateo))`, `bg-success/25`, `bg-destructive/50` — no arbitrary color values |
| `playwright-expert` | E2E mock patterns, anti-bubble base fixture | `setupHappyMocks` updated with service-day route; `assertShellMounted` before any axe scan (HB-68) |
| React patterns baseline | Error boundary, loading/error/empty states, a11y | Loading skeleton, error state, empty state on `DayAvailabilityStrip`; `role="button"` + `aria-pressed` on swimlanes; keyboard Enter/Space |

## Live verification

Not executed in this session (requires live stack + `chrome-devtools-verify`). Escalate to Chris staging gate (G phase) for live exercise of the complete flow: service+day → swimlanes render → hora filter → FreeDoctorsList filtered → lane click selects doctor.
