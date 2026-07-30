# T-G2F12-FE Result — FaqPairList / ObjecionPairList local-state (ADR-009)

**Ticket:** G2-F12-FE  
**Story:** vitalia-fase2-lisa-servicios  
**Commit:** `54119aaf`  
**Branch:** `wip/vitalia`  
**Date:** 2026-06-18

---

## Diff summary (5 files, 150 net insertions)

| File | Change |
|---|---|
| `FaqPairList.tsx` | +`useState<FaqPair[]>(initialValue)` — local state, seeded once from prop. `patch`/`remove`/`add` mutate `localPairs` + call `onChange`. Renamed prop param to `initialValue`. |
| `ObjecionPairList.tsx` | Same pattern: +`useState<ObjecionPair[]>(initialValue)`. |
| `ParaAdrianView.tsx` | Added `key={offerId}` to `<FaqPairList>` and `<ObjecionPairList>` — forces remount (clean re-seed) when user switches service. Did NOT touch `defaultValue` textareas (out of scope per ticket). |
| `__tests__/FaqPairList.test.tsx` | Added ADR-009 regression test: type in input, force parent re-render with same stale `value` prop, assert input retains typed text (not stale server value). |
| `__tests__/ObjecionPairList.test.tsx` | Same regression test for `ObjecionPairList`. |

---

## TDD — RED → GREEN

**RED (before fix):**
- `FaqPairList > ADR-009: typed text survives a parent re-render with the same stale value prop` — FAILED (value reverted to `"¿Duele?"` immediately after `fireEvent.change`)
- `ObjecionPairList > ADR-009: typed text survives a parent re-render...` — FAILED (value reverted to `"Precio"`)

**GREEN (after fix):** 12/12 tests pass in both test files.

---

## Gate output

```
tsc --noEmit         → 0 errors (no output)
eslint (3 files)     → 0 errors (no output)
vitest run (servicios/) → 22 files, 156 tests, all PASS
```

---

## Root cause (per ADR-009 §3.4 "componentes hijos que reciben value como prop desde query-data")

`FaqPairList`/`ObjecionPairList` were pure controlled components: every render they read `value` from the prop array re-derived in `ParaAdrianView`. When `useAutosave` called `setStatus` (idle→saving→saved), `ParaAdrianView` re-rendered and re-derived `value` from `brief?.faq ?? []` (stale server data) — overwriting whatever the user had typed. The `fireEvent.change` in the regression test reproduced this: the value reverted on the very next render.

**Fix:** add `useState` seeded from the `value` prop once at mount. All mutations (`patch`/`remove`/`add`) update local state directly and propagate via `onChange` for autosave. The parent's stale `value` prop is only used as the initial seed — it never overwrites local edits.

**Re-seed on entity change:** `key={offerId}` in `ParaAdrianView` forces React to remount both components when the user navigates to a different service, giving a clean local state seed from the new entity's data. This is the "hidratar una vez por entidad" pattern from ADR-009 §2.1.

---

## Scope notes

- Did NOT touch `defaultValue` textareas in `ParaAdrianView` (candidate_ideal, contraindications, etc.) — those are uncontrolled inputs and are not affected by this bug (they do not re-bind to server data on re-render).
- Did NOT touch `use-autosave.ts` (hook is correct per ADR-009 §1.2).
- Did NOT touch `ResumenView.tsx` (fixed in commit `e6f97173`, per ticket scope).
- Did NOT touch BE.

---

## Skills consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary, local state pattern, TDD Vitest, runtime quality checklist | Used `useState` local state (not RHF — array editors are simpler with direct state); `key` prop for re-seed per ADR-009 §2.1 |
| `brand-expert` | Called per system prompt for brand-studio paths | Not applicable (servicios feature, not brand-studio) |
| `offer-expert` | Called per system prompt | Not applicable |
| `offer-type-preset-expert` | Called per system prompt | Not applicable |
| `copilot-expert` | Called per system prompt | Not applicable |
| `sales-agent-expert` | Called per system prompt | Not applicable — but `FaqPairList`/`ObjecionPairList` feed Adrián KB via `sales_brief` |
| `metrics-expert` | Called per system prompt | Not applicable |
| `chrome-devtools-verify` | Would invoke for live verify — dev stack not running in this session | Escalate: Chris to verify typing fluidity live on `localhost:3002` before marking story done |

---

## Live verification note

`chrome-devtools-verify` was not invoked — the dev stack is not running in this session. Per DoD #37, **Chris must exercise the fix live** before the story closes:

1. Navigate to `localhost:3002/{tenantId}/(shell-organism)/lisa/servicios/{serviceId}/para-adrian`
2. Type multiple characters in a "Pregunta" field inside "Preguntas frecuentes"
3. Confirm: typing is fluid (no letra-por-letra lag), value does not revert
4. Add a pair, edit it, remove it — all instant feedback
5. Switch to another service — FAQ/objections should show the new service's data (key remount)

<!-- @pm: build phase done (state: tests-passing). Commit: 54119aaf. Files: 5. Native ticket tests: 12/12 PASS (regression) + 156/156 PASS (full servicios suite). Awaiting orchestrator → gate-runner → auditor-frontend (independent verdict). -->
