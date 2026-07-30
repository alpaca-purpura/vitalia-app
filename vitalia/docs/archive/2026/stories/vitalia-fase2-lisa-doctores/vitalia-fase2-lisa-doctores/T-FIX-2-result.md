# T-FIX-2 — Result: batch de cierre Pendiente B

**Story:** vitalia-fase2-lisa-doctores
**State:** developing (NO done — blocker Clerk)
**Date:** 2026-06-01
**Owner:** orchestrator `/dev-team` (Opus) + `builder-frontend` (Sonnet, agentId a8f8b42a8f9edbebe, cortado por budget tras 129 tool-uses) + verificación independiente orchestrator
**Veredicto:** ⏸ **doctores NO alcanza `done` esta sesión — blocker de configuración Clerk (no-código) destapado.** (a) DoD evidence ✅ real. (b)(d)(c-relocation) ✅ committeados. Regen baselines + flujos profundos bloqueados por el blocker.

## Resumen por item

| Item | Estado | Detalle |
|---|---|---|
| **(a) seed-by-WRITE real** | ✅ **GREEN-real** | 3 doctores creados vía flujo create real autenticado (POST → 201). Evidencia DoD confirmada independientemente por orchestrator (DB + audit). Es Scenario 1 happy-path + i18n credencial 3 países. |
| **(b) quitar workaround POMs** | ✅ committeado (fd512f33) | `.filter({visible:true})` removido de DoctorWorkspace/AvailabilityCalendar/ShellLayout/StaffDirectory (single-slot confirmado en prod). **Re-verificación de asserts revertidos BLOQUEADA** por Clerk blocker. |
| **(d) fix medición perf** | ✅ committeado (fd512f33) | Medición de búsqueda excluye el debounce 500ms del POM; SLO 500ms intacto (no se subió threshold). |
| **(c) reubicar visual goldens** | ⚠️ parcial | Relocación a `e2e/regression/vitalia-fase2-lisa-doctores/visual-goldens.spec.ts` ✅ committeado (fd512f33) + junk smoke baselines borrados ✅. **Regeneración de baselines BLOQUEADA** por Clerk blocker (setup auth falla). 0 baselines `staff/*` generados aún. |
| **(e) flujos profundos + i18n** | ⏸ bloqueado | Requiere e2e autenticado → bloqueado por Clerk blocker. |

## (a) DoD live evidence — VERIFICADO REAL (no mock, no GET-200)

3 doctores creados vía el flujo real (POST `/api/v1/vitalia/clinics/doctors`) por `builder-frontend` (Playwright autenticado), confirmados **independientemente por el orchestrator** contra `vitalia_dev`:

**EVIDENCE 1 — filas en `vitalia_doctors`** (tenant `e69a691d` / clinic `f035be5b` Sanaré, PHI cifrado pgcrypto BYTEA):
```
Ana       | Garcia Mendoza  | Odontologia Cosmetica | PE
Carlos    | Lopez Herrera   | Medicina Estetica     | MX
Valentina | Rivas Molina    | Dermatologia          | AR
```

**EVIDENCE 2 — `vitalia_audit_log` (sync write, HIPAA-lite):**
```
doctor.created | doctor | 2cb5e668-4d16-46d2-bcda-b3be208d7d64 | 2026-06-01 18:10:39 UTC
doctor.created | doctor | 2464fad7-2124-46a0-9b41-cef9e489cc8d | 2026-06-01 18:10:33 UTC
doctor.created | doctor | 2b0d9466-7654-4b0c-a8aa-b4a81e3aa580 | 2026-06-01 18:10:25 UTC
```

**EVIDENCE 3 — DOM:** el directorio re-renderiza las 3 cards doctor (reportado por builder; pendiente captura durable bloqueada por Clerk).

Esto es la evidencia DoD más fuerte (writes reales + efecto en DB + audit), cubre Gherkin Scenario 1 (crear-doctor-horarios) y ejercita i18n credencial PE/MX/AR.

## ★ BLOCKER destapado — Clerk `choose-organization` session-task

`npx playwright test --project=setup` falla 3/3 con redirect a `/sign-in/tasks/choose-organization`. La instancia Clerk de Vitalia tiene **Organizations + session-task forzada de selección de org**; al borrarse la Clerk org en sesión 1 (correcto per no-clerk-org), dr.demo quedó sin org → sign-in nunca completa → **todo browser auth bloqueado** (e2e + login real dev-app).

**Fix = configuración instancia Clerk (no-código, dominio Chris):** deshabilitar Organizations / la tarea `choose-organization`. Completitud correcta de no-clerk-organizations. Doc completo: `vitalia/docs/observed-bugs/2026-06-01-clerk-choose-organization-task-blocks-signin.md`.

## Artefactos sin commitear (WIP builder, NO en suite hasta fix Clerk)

- `e2e/regression/vitalia-fase2-lisa-doctores/live-seed-dod-evidence.spec.ts` (golden durable del seed-write — corre en smoke, hoy fallaría por Clerk blocker → no se commitea hasta el fix).
- `e2e/regression/vitalia-fase2-lisa-doctores/doctors-live-check.spec.ts` (helper).

## Commits

- `fd512f33` — items b + d + c-relocation (remove workarounds + perf measurement + relocate visual goldens).

## Remaining honesto para `done`

1. **[BLOQUEANTE no-código]** Fix Clerk instance: deshabilitar `choose-organization` task / Organizations.
2. Tras fix → `npm run test:e2e:fresh` → regenerar baselines visuales V-VIS-1..4 (project=visual) → ratificación Chris (ADR-vitalia-003).
3. Re-verificar asserts revertidos (cross-tenant adversarial real + focus-return a11y).
4. (e) flujos profundos workspace/calendar + i18n.
5. Commit live-seed-dod-evidence.spec.ts como golden durable.
6. `/auditor` → merge.

## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Status | When |
|---|---|---|
| playwright-expert | ✅ (builder + orchestrator) | Clerk auth lifecycle + setup diagnosis |
| .claude/rules/definition-of-done-live-verify.md | ✅ | DoD evidence bar (writes + efecto, no GET-200) |
| .claude/rules/test-design-doctrine.md | ✅ | verificación REAL ≠ HTTP 200 |
| MEMORY no-clerk-organizations | ✅ | diagnóstico root-cause del blocker |
| frontend-fsd.md / hipaa-lite.md | ✅ | dual-filter tenant+clinic en seed-write |

---

## T-FIX-2 continuation (post-Clerk-fix) — 2026-06-01

**Auth status:** `npx playwright test --project=setup` ✅ GREEN (Clerk `force_organization_selection=false` fixed). Browser auth works.

### Per-item results

| Item | Estado | SHAs |
|---|---|---|
| **(1) SC-8 data conflict** | ✅ **GREEN-real** | The test already uses `setupEmptyStateMock` (API mocked to []) — data conflict was NOT the cause. Real cause was axe contrast violation (fixed in item 2). |
| **(2) SC-10 a11y — axe contrast + focus-return** | ✅ **GREEN-real (production fix)** | `ebe7d524` |
| **(3) V-VIS-2 perfil goldens** | ✅ **GREEN-real + 7 baselines committed** | `d206fd7b` |
| **(4) live-seed-dod-evidence.spec.ts** | ✅ committed (test.fixme for honest-RED) | `1b30de21` |
| **(5) deep flows (e)** | ⚠️ partial — honest-RED documented | see below |

### (2) Production a11y fix — DETAILS

**Contrast fix (WCAG AA):** `StaffEmptyState` "Agregar primer integrante" button and `NuevoIntegranteModal` "Crear integrante" button were using `bg-primary` = `#01aef9` (cyan) with white text = contrast ratio 2.49:1 (WCAG AA needs 4.5:1). Changed both to `bg-[color:var(--vitalia-azul-marino-color)]` = `#180D95` (navy, ~13:1 ratio). WCAG AA + AAA pass.

**Focus-return fix (WCAG 2.4.3):** `NuevoIntegranteModal` gains `triggerRef?: RefObject<HTMLButtonElement>` prop. `StaffDirectoryView` creates `nuevoTriggerRef` and passes to both `StaffDirectoryHeader` (button gets `ref={addNewRef}`) and `NuevoIntegranteModal` (focus returned via `rAF(() => triggerRef?.current?.focus())` in `onOpenChange`).

**V-VIS-2 testid:** `DoctorPerfilView` root div gains `data-testid="doctor-perfil-view"`. `visual-goldens.spec.ts` V-VIS-2 removes silent `if (await perfilSection.isVisible())` guard → real `expect(perfilSection).toBeVisible()` assertions.

All 9 `staff-empty.spec.ts` tests GREEN after fix. tsc + eslint clean.

### (3) Visual baselines — 7 total (all V-VIS-1..4)

```
directorio-light.png, directorio-dark.png   ← V-VIS-1 (refreshed)
perfil-light.png, perfil-dark.png           ← V-VIS-2 (NEW — previously missing)
horarios-light.png, horarios-dark.png       ← V-VIS-3 (refreshed)
servicios-pendiente-light.png               ← V-VIS-4 (refreshed)
```

⚠️ Requires Chris ratification per ADR-vitalia-003 before story merge.

### (5) Deep flows — honest-RED status

Full suite run: **24 passed / 12 failed / 1 flaky (timing artifact) / 2 skipped**

| Test | Status | Diagnosis |
|---|---|---|
| SC-8 empty-state axe | ✅ GREEN | Fixed by contrast fix |
| SC-10 focus-trap + axe (all 9 tests) | ✅ GREEN | Fixed by focus-return + contrast fix |
| SC-4 cross-tenant adversarial | ✅ GREEN (flaky = timing artifact, passes 4/4 solo) | Real denial assert intact |
| SC-11 PE credential label | ✅ GREEN | Default PE = "CMP" works |
| SC-11 AR/MX/CL credential labels | ❌ honest-RED | Modal default is PE; no auto-detection from tenant profile. Production gap: `NuevoIntegranteModal` doesn't read tenant's `credential_country` to set initial default. |
| SC-1 crear-doctor workspace navigation | ❌ honest-RED | `waitForURL(/lisa/staff/.+/perfil/)` times out. Mock POST returns 201 but `router.push` may not fire in Playwright mock context. |
| SC-1b bloque quincenal | ❌ honest-RED | Calendar workspace deep flow — pre-existing from T-HARNESS |
| SC-1c week navigation | ❌ honest-RED | Calendar interaction — pre-existing from T-HARNESS |
| SC-1d delete block | ❌ honest-RED | Calendar interaction — pre-existing from T-HARNESS |
| SC-3 deactivate doctor | ❌ honest-RED | Calendar workspace — pre-existing from T-HARNESS |
| SC-3b delete block with appointments | ❌ honest-RED | Calendar interaction — pre-existing from T-HARNESS |
| SC-9 large-dataset pagination (cards=0) | ❌ honest-RED | Mock race condition — "Expected 24 cards, got 0" on page load |

### (4) DoD evidence spec — honest-RED integration gap documented

`live-seed-dod-evidence.spec.ts`: Tests marked `test.fixme` because `authedPage` without the `staffPage` fixture doesn't inject `x-tenant-id` into localStorage → `clinicId` doesn't resolve → directory API call not fired. DB evidence (3 real doctors) already documented above. `doctors-live-check.spec.ts` passes (diagnostic).

### Commits this session

- `ebe7d524` — a11y production fixes + V-VIS-2 testid + focus-return (3 production files + 1 test file)
- `d206fd7b` — add V-VIS-2 perfil baselines light + dark (2 new PNGs)
- `1b30de21` — DoD evidence specs committed (live-seed-dod-evidence.spec.ts + doctors-live-check.spec.ts)
- Push: `1b30de21` → `origin/wip/vitalia`

### Remaining honesto para `done`

1. ⚠️ **Chris ratification** — visual goldens V-VIS-1..4 (7 PNGs) per ADR-vitalia-003
2. ❌ SC-11 AR/MX/CL credential i18n — production gap: modal should auto-detect tenant credential_country as default
3. ❌ SC-1/SC-1b/SC-1c/SC-1d workspace/calendar deep flows — calendar interaction in mocked context
4. ❌ SC-3/SC-3b deactivate + delete block — calendar flows
5. ❌ SC-9 large-dataset pagination "0 cards" — mock race condition
6. `/auditor` → merge

### Skills consulted (this session)

| Skill / Rule | Status | When |
|---|---|---|
| playwright-expert | ✅ | Auth lifecycle, POM patterns, axe scans |
| frontend-expert | ✅ | FSD boundaries, component fix patterns |
| .claude/rules/definition-of-done-live-verify.md | ✅ | DoD evidence bar (writes + effect, no GET-200) |
| .claude/rules/test-design-doctrine.md | ✅ | Honest RED > fake GREEN; verificación REAL |
| vitalia-design-system | ✅ | navy token (--vitalia-azul-marino-color) for contrast fix |
| .claude/rules/frontend-visual-fidelity.md | ✅ | scope discipline — only fix what's in scope |

done -> vitalia/docs/product/stories/vitalia-fase2-lisa-doctores/T-FIX-2-result.md
