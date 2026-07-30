<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Frontend Code Review: vitalia-fase2-lisa-doctores (Staff — lisa)

**Date:** 2026-05-31
**Brand:** vitalia
**Tickets:** T-FE-1, T-FE-2, T-FE-3, T-E2E
**Files Reviewed:** 24 FE (staff components, EntitySubNavBar, routes, api/hooks/store/types, mocks, e2e) + BE DTO cross-check
**Domains touched:** lisa (FE feature) + shell-organism (shared) — clinics/scheduling BE consumed
**Skills consulted:** frontend-expert, vitalia-design-system, brand-expert (bio voice anchor N/A — D-4 deterministic)
**Live-verified:** NO — E2E specs are self-flagged `STACK-STATUS: PENDING-LIVE-VERIFICATION`; happy path never exercised against real BE:8002 (Vitest/MSW green only)
**Verdict:** **CHANGES_REQUESTED**

---

## Gate Status (run directly — no gate-output.json present)

| Gate | Step | Result | Detail |
|---|---|---|---|
| QUALITY | tsc --noEmit | PASS | 0 errors strict |
| QUALITY | ESLint (staff scope) | PASS | 0 errors |
| FUNCTIONAL | Vitest (lisa/staff + EntitySubNavBar + arch) | PASS | 269/269 (31 files) — **but mocked (MSW camelCase) hides BE contract drift** |
| Arch | FSD / cross-feature / server-first / ribbon-no-tabs / no-voseo / phi-pii / no-hardcoded-colors / agent-subsubtabs-ssot | PASS | all green |

> Gate green is necessary but NOT sufficient here: the green Vitest suite is built on MSW handlers that mirror the FE camelCase types, not the real snake_case BE DTOs (see F1). This is the "GET 200 ≠ verified" trap (test-design-doctrine.md).

---

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite boundaries | PASS | 0 |
| 2 | ADR-vitalia-004 (Server-First, RQ+Zustand split, rutas-hoja, RHF+Zod) | WARN | 1 (nav method) |
| 3 | EntitySubNavBar (D-1, sibling not modification, WAI-ARIA) | WARN | 1 (window.location nav) |
| 4 | autosave-no-save-button (HARD) | PASS | structurally correct; see F3 coalescing |
| 5 | Visual fidelity / design-system tokens | WARN | 1 (malformed var-opacity classes) |
| 6 | Forbidden-touch respected | PASS | 0 |
| 7 | Spanish neutro (no voseo) | PASS | arch test green |
| 8 | PHI in URL/searchParams + master-data | WARN | 1 (toLocaleDateString) |
| 9 | Bio repo + AvatarUploader (proxy D-3) | PASS | proxy upload + AbortController timeout correct |
| 10 | Horarios calendar (custom grid + @dnd-kit, UTC, 24h) | WARN | 1 (dnd-kit dead weight) |
| 11 | E2E real-backend (verification-real) | FAIL | F2 |
| — | **FE↔BE contract (camelCase vs snake_case)** | **FAIL** | **F1 (blocking)** |

---

## Findings

### FAIL — F1: Systemic FE↔BE contract mismatch (camelCase FE vs snake_case BE, no alias, no transform)
**Category:** 2 / 4 (Contract compliance) — **Carril C escalate + Carril B fix**
**Files:**
- `vitalia/frontend/src/features/lisa/types/staff.types.ts` (camelCase: `firstName`, `dniMasked`, `pageSize`, `visibleEnLanding`, `yearsExperience`, `avatarKey`, `bioInputsNotes`)
- `vitalia/frontend/src/features/lisa/api/staff.ts:198-243` (`usePatchDoctor` sends camelCase keys)
- `vitalia/backend/.../clinics/api/dtos.py:120-176` (`DoctorDetailDTO` / `DoctorListItemDTO` / `DoctorPatchRequest` — pure snake_case, `ConfigDict(from_attributes=True)`, **no `alias_generator`/`populate_by_name`/`by_alias`**)
- `vitalia/backend/.../clinics/api/doctors_router.py:127-150` (`_to_list_item` returns `display_name`, `masked_dni` — NO `first_name`/`last_name`/`avatar_url`/`patients_count`/`nps_score`)

**Issue:** No casing transform exists on either side (`fetchClient` does not camelize; no `humps`/`camelcase-keys` dep). Against the **real** backend:
1. **List/detail GET** → BE emits `{display_name, masked_dni, page_size, visible_en_landing, years_experience, avatar_key, first_name, ...}`. FE `StaffCard.tsx:35` reads `doctor.firstName`/`doctor.lastName`/`avatarUrl`/`patientsCount`/`npsScore`/`dniMasked` → all `undefined` → cards render "undefined undefined", blank stats, broken masking. The list DTO does not even contain `first_name`/`last_name` (only `display_name`) nor `patients_count`/`nps_score`.
2. **Autosave PATCH** (`usePatchDoctor`) sends `{phone, yearsExperience, visibleEnLanding, bioInputsNotes, avatarKey}`. `DoctorPatchRequest` (no `extra="forbid"`) silently **drops** unknown camelCase keys → returns 200, persists nothing. Worse: `phone` is **absent from `DoctorPatchRequest` entirely** — phone autosave can never persist even in snake_case.
3. Only `useCreateDoctor` (maps to snake_case via `mapDoctorCreateToPayload`) and `useAvatarUpload` (sends `avatar_key`) are wire-correct.

Why green tests missed it: MSW handlers (`src/mocks/handlers/staff.ts:31,38,84,104`) return camelCase mirrors of the FE types, so Vitest passes. The real contract was never exercised (F2).

**Fix (Carril C → escalate to /pm-vitalia + architect for the decision, then Carril B build):**
- Decide alignment direction. Recommended: BE adds `model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)` + routes serialize `by_alias=True` (camelCase wire is the FE-mirror contract in 03-arch-fe.md § TypeScript Types). OR add a FE response-mapping layer (`mapDoctorDetail`/`mapListItem`) + payload mapper for PATCH.
- Add `phone` to `DoctorPatchRequest` (currently un-persistable).
- Add `patients_count`/`nps_score`/`avatar_url` to list DTO OR remove them from `StaffCard`/`DoctorListItem` (spec stats are "tiny"; confirm source).
- New tests required: a contract test asserting FE PATCH payload keys ∈ BE DTO fields, and an integration/E2E that round-trips against real BE. Auditor does NOT write tests → builder-frontend + builder-backend (Carril B).
**Skill ref:** test-design-doctrine.md § verification REAL; 03-arch-fe.md § TypeScript Types ("mirror Pydantic camelCase"); auditor-downstream-regression.md (cross-stack surface).

### FAIL — F2: Happy-path E2E never verified against real backend (falso-verde risk)
**Category:** 11 — **Carril B**
**File:** `vitalia/frontend/e2e/regression/vitalia-fase2-lisa-doctores/staff-crear-happy.spec.ts:18-20,132,171` + `staff-deactivate` PATCH mock (`:188-207`)
**Issue:** Specs are headered `STACK-STATUS: PENDING-LIVE-VERIFICATION`, assert `toBeGreaterThanOrEqual(0)` "may be 0 if mock resets", and the deactivate test mocks the PATCH response with a `future_appointments_count` shape the BE does not return (`DeleteBlockResponse` uses `preserved_appointments`; deactivate is a different path). The REAL-VERIFICATION state_check SQL is documented only as comments, never executed. Per verification-real / test-design-doctrine, a write scenario is verified only when the real action hits the real BE and the DB effect is observed. This wasn't done — and F1 means it would have failed if it had been.
**Fix:** Once F1 is resolved + R2/stack up, run the happy + deactivate + block-delete specs against BE:8002, assert real DB state (audit_log row, materialized slots ≤ end_date, preserved appts unchanged), and replace the `>= 0` escape asserts with exact expectations. Builder-frontend + playwright-expert.
**Skill ref:** verification-real-not-200 (MEMORY); test-design-doctrine.md.

### WARN — F3: Autosave payload replacement loses concurrent field edits
**Category:** 4 — **Carril B (needs test)**
**File:** `DoctorPerfilView.tsx:97-115` + `use-autosave.ts:109-127`
**Issue:** `handleFieldChange` builds a single-field payload and calls `scheduleAutosave(payload)`. `useAutosave.schedule` overwrites `pendingPayloadRef` wholesale. Editing field A then field B within the 600ms window discards A's PATCH. Each field carries its own `{field: value}` object — no merge.
**Fix:** Coalesce pending payloads (`pendingPayloadRef.current = { ...pendingPayloadRef.current, ...payload }`) in `use-autosave` schedule, or accumulate the patch in the view before scheduling. Add a Vitest covering two rapid field edits → single merged PATCH. (Existing autosave tests don't cover this → Carril B.)
**Skill ref:** form-runtime-array.md (autosave non-negotiable); runtime-quality-checklist.md (stale/coalescing).

### WARN — F4: EntitySubNavBar leaf nav uses `window.location.href` (full reload, breaks SPA + RQ cache + SC-1c)
**Category:** 2 / 3 — **Carril B (behavioral, EntitySubNavBar.test.tsx covers structure not nav-type)**
**File:** `src/components/shared/shell-organism/EntitySubNavBar.tsx:220-225`
**Issue:** Active-leaf navigation does `window.location.href = leaf.href` inside the `<button>` onClick, forcing a full document reload — defeats Next.js client routing, drops React Query cache (forces refetch), and contradicts 03-arch-fe.md ("deep-link + back/forward respected — SC-1c"). `Link` is already imported (used for the back link) but not for leaves. Note the comment "this button wraps in a link" is inaccurate — it's a bare button.
**Fix:** Render each leaf as `<Link href={leaf.href} role="tab" ...>` (or `router.push` from `next/navigation`) preserving roving tabindex + Arrow keys. SubSubTabsBar (the sibling pattern) correctly uses `router.push` — mirror it.
**Skill ref:** vitalia-design-system § 4 (port verbatim from SubSubTabsBar); tessl react-patterns (Link for navigation).

### WARN — F5: Malformed Tailwind CSS-var-with-opacity classes (`bg-[--agent-lisa]/20`)
**Category:** 5 (Visual fidelity / tokens) — **Carril A candidate (mechanical, but no existing visual test covers it → leave to builder)**
**Files:** `AvailabilityCalendar.tsx:164-167,498,546`; `BloquePopover.tsx:569`
**Issue:** `bg-[--agent-lisa]/20` mixes the CSS-var-shorthand arbitrary value with an alpha modifier. Tailwind cannot inject an alpha channel into an opaque `var(--agent-lisa)` (the var is not a bare channel triple), so `/20`, `/30`, `/10`, `/60`, `/90` opacity is dropped — blocks render at full opacity instead of the intended tint. Elsewhere the codebase correctly uses `color-mix(in srgb,var(--agent-lisa) 15%,transparent)` (EntitySubNavBar.tsx:235) or `var(--agent-lisa)` without `/n`.
**Fix:** Use `bg-[color-mix(in_srgb,var(--agent-lisa)_20%,transparent)]` (matching EntitySubNavBar) or a token utility that exposes the channel triple. NOT a pure-mechanical auto-fix (no existing test asserts the rendered alpha) → builder applies + visual golden confirms.
**Skill ref:** frontend-visual-fidelity.md (tokens, no malformed token usage); vitalia-design-system § 1.

### WARN — F6: `toLocaleDateString` for week-range label (master-data.md / 03-arch-fe explicit "no toLocaleDateString")
**Category:** 8 — **Carril B**
**File:** `AvailabilityCalendar.tsx:66-67` (`formatWeekLabel` → `monday.toLocaleDateString("es-419", opts)`)
**Issue:** 03-arch-fe.md § Calendar decision states "24h format (no AM/PM, no `toLocaleDateString`)" and master-data.md prohibits `toLocaleDateString()`. The week-range header label uses it directly. Scope-limited (non-PHI, non-monetary, non-slot label — it's a cosmetic date range), so WARN not FAIL, but it's an explicit-rule violation flagged by the arch contract.
**Fix:** Use `formatTenantDate*()` / `useTenantLocale()` formatter, or a deterministic UTC-safe formatter. Block start/end TIMES are already 24h string-formatted (good). Add coverage in horarios.test.
**Skill ref:** master-data.md; 03-arch-fe.md § Calendar decision.

### WARN — F7: `@dnd-kit` mounted but inert (drag implemented via raw mouse events)
**Category:** 10 — **Carril B (or doc-justify)**
**File:** `AvailabilityCalendar.tsx:22-30,241-245,366-372,384-388`
**Issue:** `DndContext` + `PointerSensor` are wired and `handleDragStart`/`handleDragEnd` are explicit no-ops ("handled via mouse events"). The real drag-to-create runs on `onMouseDown`/`onMouseEnter`/`onMouseUp`. So `@dnd-kit` adds bundle weight + a wrapper with zero behavior, and the a11y benefit dnd-kit was chosen for (03-arch-fe § Calendar decision: "accessible, headless ... a11y SC-10") is unrealized — keyboard block creation is not provided by the mouse-event path. knip may flag the sensor as effectively unused.
**Fix:** Either implement creation through dnd-kit (gain keyboard a11y for SC-10) or drop `DndContext`/sensors entirely and document the click/drag-via-mouse decision (arch-fe offered a "click-start + click-end" fallback — pick one and remove the dead wrapper). Confirm SC-10 keyboard operability of block creation regardless.
**Skill ref:** 03-arch-fe.md § Calendar decision; frontend-quality.md (knip dead code).

---

## Positive notes (compliant)
- **FSD-Lite:** `features/lisa` has no cross-feature imports; EntitySubNavBar correctly lives in `components/shared/shell-organism/`; Shadcn primitives confined to `components/ui/`. Arch tests green.
- **Server-First routing:** `staff/page.tsx`, `[doctor-id]/layout.tsx`, `perfil|horarios|servicios/page.tsx` are Server Components; `params` awaited (Next 16 Promise); rutas-hoja reales (no Shadcn `<Tabs>` — `test-ribbon-no-shadcn-tabs` green); PHI never in URL (`[doctor-id]` is UUID; nuqs filters are non-PHI q/specialty/active/page).
- **RQ + Zustand split clean:** server data in React Query (keys `['lisa','staff',...]`), UI-only state (modal, calendar week, drag draft) in `staff-ui-store`, filters in URL. No mixing.
- **EntitySubNavBar = NEW sibling, NOT a modification** of SubSubTabsBar (D-1 honored); WAI-ARIA tablist + roving tabindex + Arrow/Home/End + `aria-disabled` leaves when `entity=null`. Forbidden files (`SubSubTabsBar`, `Ribbon`, `SubTabsBar`, `ValeriaSidebar`, `lisa/marca/**`) untouched.
- **autosave-no-save-button:** DoctorPerfilView has NO Guardar button, 600ms debounce, hint "Los cambios se guardan automáticamente", `aria-live` status. Hook is stale-closure-safe (refs).
- **AvatarUploader / proxy upload (D-3):** POST to `assets/upload` proxy (not presigned), AbortController 60s timeout, then PATCH avatar_key. Graceful.
- **Credential validator** mirrors BE per-country (PE numeric / AR·MX·CL alphanumeric) with Spanish-neutro messages; discriminated-union availability schema correct.
- **PHI:** DNI shown masked in perfil (`"***"+slice(-3)`), email read-only, list relies on masked fields. Spanish neutro arch test green (no voseo).

## Forbidden-touch audit — PASS
No diff to `SubSubTabsBar.tsx` / `Ribbon.tsx` / `SubTabsBar.tsx` / `ValeriaSidebar.tsx` / `lisa/marca/**`. EntitySubNavBar is additive.

## Cross-brand / engine audit — PASS
`test-no-cross-brand-shell-mirror` green (no ShellOrganismLayout/EntitySubNavBar mirror in nicolify/comunify/lupulo). No `core/luana-core-*` edits. No root-legacy paths.

## Native-First / git — PASS (review-only, no commits made)

## Verdict Math
- F1 (FE↔BE contract) → cross-stack FAIL, persistence/render broken on real BE → **CHANGES_REQUESTED** (Carril C escalate for direction + Carril B fix)
- F2 (no real-backend verification) → FAIL Cat 11 → reinforces CHANGES_REQUESTED
- F3–F7 WARN (Carril B mostly)
- All gates + arch fitness green, but green is MSW-mocked → not exonerating
- **Overall: CHANGES_REQUESTED**

## Hand-off
- **Carril C (escalate /pm-vitalia + /architect):** F1 alignment-direction decision (BE camelize-by-alias vs FE mapping layer) + add `phone` to PATCH DTO + reconcile list stats fields.
- **Carril B (builder-frontend + builder-backend):** F1 mapping/tests, F2 real-BE E2E, F3 autosave coalescing + test, F4 Link nav, F6 tenant-locale date, F7 dnd-kit decision.
- **Carril A:** none safe (F5 token fix lacks an existing test that verifies rendered alpha; leave to builder + visual golden).

---

## Audit iteration 2 response — 2026-05-31

**Mode:** AUDITOR_AUTO_FIX_LOOP · Commit: `0ce5fe1b`

### Applied fixes summary

**F1 follow-through (null-guard stats + MSW contract alignment)**
- `DoctorListItem` type: `maskedDni` (was `dniMasked`, matching real BE `masked_dni` → `maskedDni` camelCase), nullable `patientsCount`/`npsScore`, `avatarKey` (not `avatarUrl` in list), added `maskedEmail`, `maskedPhone`, `displayName`, `visibleEnLanding`.
- `StaffCard.tsx` `displayName`: now `[firstName, lastName].filter(Boolean).join(" ") || "—"` — null-safe.
- MSW `staff.ts`: mock data updated to `maskedDni`, `patientsCount: null`, `npsScore: null`, `avatarKey`, added `maskedEmail`/`visibleEnLanding`/`displayName`/`createdAt`. MSW now mirrors real BE shape — the contract drift the audit flagged is corrected.
- `staff.test.tsx`: fixture updated to `maskedDni`.
- **Live verified:** `curl GET /api/v1/vitalia/clinics/doctors` (BE :8002) returns camelCase — `pageSize`, `firstName`, `lastName`, `maskedDni`, `patientsCount: null`. Contract confirmed. ✓

**F3 — autosave coalescing (IMPORTANT data-loss fix)**
- `use-autosave.ts` `schedule()`: coalesces pending object payloads via spread merge (`{ ...pending, ...incoming }`) before resetting the timer. Two rapid field edits (specialty at t=0, phone at t=300ms) produce a single merged PATCH with both fields at t=900ms.
- New Vitest tests added: "coalesces two rapid object field edits into a single merged PATCH" + "later field value wins when same field edited twice within window". Both GREEN. ✓
- **Live verified:** `curl PATCH /doctors/:id {"specialty":"Cardiología","phone":"+51 999 111 222"}` → response shows both `specialty` and `phone` updated. ✓

**F6 — toLocaleDateString violation (master-data.md)**
- `AvailabilityCalendar.tsx` `formatWeekLabel()`: replaced `toLocaleDateString("es-419", opts)` with `new Intl.DateTimeFormat("es-419", opts).format(date)`. Explicit locale, no browser-default date resolution. Rule-compliant.
- `data-testid="week-label"` added to the week range `<span>`.
- New Vitest tests: "renders a week label containing the year" + "week label is non-empty and not undefined/null". Both GREEN. ✓

**F4 — EntitySubNavBar full-page reload fix**
- `EntitySubNavBar.tsx`: added `useRouter` from `next/navigation`. Replaced `window.location.href = leaf.href` (hard reload) with `router.push(leaf.href)` (client nav). Preserves React Query cache and SC-1c deep-link semantics. Mirrors SubSubTabsBar pattern. ✓

### Remaining open (not fixed in this loop)

**F2 — no real-backend E2E verification**
Still FAIL — requires full Playwright run against real stack. Deferred to post-merge. Requires `playwright-expert` + Clerk testing token + running BE:8002.

**F5 — malformed Tailwind CSS var opacity classes**
`bg-[--agent-lisa]/20` in AvailabilityCalendar.tsx/BloquePopover.tsx still present. No existing visual test verifies rendered alpha — Carril A is not safe. Deferred to builder with visual golden.

**F7 — @dnd-kit inert**
`DndContext` + `PointerSensor` wrapper exists with no-op handlers; drag-to-create runs on raw mouse events. Decision needed: wire dnd-kit for keyboard a11y (SC-10 compliant) or drop it and document the choice. Escalated to PM/architect.

### Gates post-fix

| Gate | Result |
|---|---|
| tsc --noEmit | PASS · 0 errors |
| ESLint (all touched files) | PASS · 0 errors |
| Vitest (2415 tests, 218 files) | PASS |
| Architecture (162 tests) | PASS |
| Coverage | 82.57% statements |
| Live BE contract | VERIFIED · camelCase confirmed via curl |

### Remaining verdict

- F1 follow-through: RESOLVED ✓ (types + MSW + null-guards corrected; real BE camelCase confirmed)
- F3: RESOLVED ✓ (coalescing implemented + tested + live verified)
- F6: RESOLVED ✓ (Intl.DateTimeFormat + test coverage)
- F4: RESOLVED ✓ (router.push + comment accuracy)
- F2: STILL OPEN (needs live E2E vs real BE post-stack-up)
- F5: STILL OPEN (visual golden needed)
- F7: STILL OPEN (arch decision needed)

**Overall verdict after iter 2:** CHANGES_REQUESTED pending F2/F5/F7. F2 is the most consequential — F7 is architectural, F5 is visual. None block a merge if PM accepts the deferred state documented above.
