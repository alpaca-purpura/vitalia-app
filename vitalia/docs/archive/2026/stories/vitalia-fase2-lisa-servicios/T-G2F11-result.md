# T-G2F11 — Autosave Rich Fields RHF-Bound (ADR-vitalia-009)

## Result

**Status:** DONE — gates green, commit pushed.
**Commit:** `e6f97173`
**Branch:** `wip/vitalia`

## Root cause confirmed

`value={servicio.X ?? ""}` on 15 rich textareas bound directly to react-query data.
`useAutosave.setStatus("saving"→"saved")` triggers re-render → value reverts to server
data on each keystroke. Fix invariant (ADR-009 §2.1): all editable inputs must bind
`value` to RHF local state (`field.value`), never to query data.

## Files changed

| File | Change |
|---|---|
| `vitalia/frontend/src/features/lisa/components/servicios/leaves/ResumenView.tsx` | Task 1+2: schema + 15 Controller migrations |
| `vitalia/frontend/src/features/lisa/components/servicios/leaves/__tests__/ResumenView.test.tsx` | Task 4: regression test (RED→GREEN) |
| `vitalia/frontend/src/__tests__/architecture/test-autosave-value-from-local-state.test.ts` | Task 3: arch-fitness gate (ADR-009 §3.3) |

## Task summary

### Task 1 — Schema extension
`resumenSchema` extended with 15 fields as `z.string().nullable().optional()`:
`description_long · includes · excludes · warranty · procedure_steps · anesthesia_pain ·
prep · aftercare · downtime · expected_result · result_timing · result_lifespan ·
realistic_expectations · risks · red_flags`

### Task 2 — RHF Controller migration
All 15 fields added to `defaultValues` + `form.reset()` in `useEffect([servicio?.offer_id])`.
Each textarea/input wrapped in `<Controller>` with:
- `value={field.value ?? ""}`
- `onChange={(e) => { field.onChange(e); schedule({ X: e.target.value || null }); }}`
All `value={servicio.X ?? ""}` direct bindings removed.

Out of scope (left as-is per ADR §4.1): VariantsRepeater, NumberWithUnit, session/recurrence interval Selects, initial_appt_duration.

### Task 3 — Arch-fitness gate
`test-autosave-value-from-local-state.test.ts`:
- Scans all `.tsx` importing `useAutosave`
- Flags editable inputs (`Input|Textarea|input|textarea`) with `value={ident.member}` where root ∉ `{field, form}`
- `KNOWN_AUTOSAVE_VALUE_FROM_QUERY` allowlist (shrink-only ratchet, currently empty)
- ResumenView.tsx NOT in allowlist after fix → test passes

### Task 4 — Regression test (RED→GREEN)
`ResumenView.test.tsx` — new test in `G2-F11` describe block:
- Spies on `useAutosave` to override module implementation (cycling status)
- Types text in `description_long` textarea
- Forces re-render via `rerender()`
- Asserts `textarea.value === "Texto escrito por el usuario"` (not server value)
- Was RED before fix (value would revert to `"Valor del servidor"`), GREEN after

## Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | 0 errors |
| `eslint` on changed files | 0 errors |
| `vitest run` target files | 22/22 passed (21 prior + 1 regression) |
| Arch-fitness (new test) | PASS — 0 violations |
| Pre-existing `test-no-div-layout` | Pre-existing failure (305 > 301 baseline) — NOT introduced by this PR (verified via git stash) |

## Live-verify

Chris to exercise in dev-app.vitalialat.com. The autosave laggy loop should be resolved:
typing in any rich text field (description_long, includes, procedure_steps, etc.) should
maintain cursor position and not revert to server data between keystrokes.

## Skills consulted

- `frontend-expert` — RHF Controller pattern, React patterns baseline
- `tdd-mandatory` — regression test RED first
- ADR-vitalia-009 — authoritative spec for this fix (scope/pattern/gate design)
