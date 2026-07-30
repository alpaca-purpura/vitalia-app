# T-E2E Result — vitalia-fase2-lisa-doctores

**Ticket:** T-E2E — Playwright E2E SC-1..SC-11 + axe wcag2aa + visual goldens + i18n credencial multi-locale
**Builder:** builder-frontend (Sonnet 4.6)
**Date:** 2026-05-31
**Status:** `specs-written` (state in 06-tickets.yaml updated)

---

## § Skills Consulted

| Skill | Por qué | Decisión tomada |
|---|---|---|
| `playwright-expert` | SSoT para Clerk auth fixture, POM patterns, network mocking, real verification | auth.fixture.ts pattern + page.route (legitimate mock for error-path testing only); happy-path writes NOT mocked (real BE contract); base.extend() fixture pattern para StaffFixtures |
| `frontend-expert` | FSD-Lite boundaries, runtime-quality-checklist, studio section pages | Spec files in `e2e/regression/vitalia-fase2-lisa-doctores/` + `e2e/shell-organism/staff-*.spec.ts`; POMs in `e2e/pages/`; fixture in `e2e/fixtures/` |
| `vitalia-design-system` | Shell-organism component context (EntitySubNavBar, StaffDirectoryView, workspace routes) | Locators use data-testid matching component structure from 03-arch-fe.md; no direct component reads needed |
| `tessl__react-patterns` | Error boundaries, loading/error/empty states on every async UI, accessible markup | SC-7 error banner + Reintentar; SC-8 empty-state; SC-10 axe wcag2aa scoped assertions |
| `chrome-devtools-verify` | Live verification gate | Stack DOWN (BE:8002 + FE:3002 unavailable — machine restarted + pre-existing zustand workspace resolution bug). Cannot invoke. Escalated to Chris staging gate (see § Live-run status). |

---

## § Live-Run Status: PENDING-STACK

The vitalia dev stack is DOWN:
- BE:8002 — down (machine restarted)
- FE:3002 — returns 500 (pre-existing bug: zustand workspace resolution from `core/@luana/hooks` fails with Turbopack)
- Documented: `vitalia/docs/observed-bugs/2026-05-31-zustand-workspace-resolution-luana-hooks.md`

**DO NOT fake-green.** Specs are written to verify-for-real WHEN the stack is up.
Visual golden baselines cannot be generated without FE:3002 live.

### Command to run once stack is healthy

```bash
# Prerequisites:
# 1. Fix zustand workspace resolution (ADR-vitalia-008)
# 2. make dev-vitalia  →  BE:8002 + FE:3002 both healthy
# 3. docker exec luana-vitalia-backend-dev alembic upgrade head

# Run all story specs (41 tests):
cd vitalia/frontend
E2E_BASE_URL=http://localhost:3002 E2E_TENANT_ID=<tenant_a_id> npx playwright test \
  regression/vitalia-fase2-lisa-doctores/ \
  shell-organism/staff-cross-tenant-adversarial.spec.ts \
  shell-organism/staff-deactivate.spec.ts \
  shell-organism/staff-delete-block-preserve.spec.ts \
  shell-organism/staff-empty.spec.ts \
  shell-organism/staff-large-dataset.spec.ts \
  --project=smoke

# Generate visual golden baselines (run AFTER first live pass):
E2E_BASE_URL=http://localhost:3002 npx playwright test \
  shell-organism/staff-large-dataset.spec.ts \
  --project=smoke --update-snapshots
```

### State_check DB queries (run post live E2E to verify-for-real)

SC-1 audit + slots:
```sql
-- Audit log created
SELECT action FROM audit_log
WHERE entity='doctor' AND action='created' AND tenant_id=:tenantId
ORDER BY created_at DESC LIMIT 1;
-- EXPECT: "created"

-- Slots within fecha-fin (NOT beyond)
SELECT max(slot_date) FROM availability_slots
WHERE doctor_id=:doctorId AND tenant_id=:tenantId;
-- EXPECT: <= endDate del bloque
```

SC-1b: exactly 6 biweekly occurrences:
```sql
SELECT count(distinct slot_date) FROM availability_slots
WHERE doctor_id=:doctorId AND block_id=:blockId;
-- EXPECT: 6
```

SC-1c: 1 one-off slot_date:
```sql
SELECT count(distinct slot_date) FROM availability_slots
WHERE doctor_id=:doctorId AND block_id=:oneOffBlockId;
-- EXPECT: 1
```

SC-1d: 0 future slots after block delete:
```sql
SELECT count(*) FROM availability_slots
WHERE block_id=:b2 AND slot_date >= current_date;
-- EXPECT: 0
```

SC-3: doctor deactivated, appointments preserved:
```sql
SELECT active FROM doctors WHERE id=:doctorId;
-- EXPECT: false

SELECT count(*) FROM appointments
WHERE doctor_id=:doctorId AND start_ts > now() AND status!='cancelled';
-- EXPECT: 2 (unchanged)
```

SC-3b: confirmed appointments preserved after block delete:
```sql
SELECT count(*) FROM appointments
WHERE block_origin=:blockId AND status='confirmed' AND start_ts > now();
-- EXPECT: 1 (preserved)
```

SC-4: cross_tenant_attempt audit:
```sql
SELECT action FROM audit_log
WHERE action='cross_tenant_attempt' AND tenant_id=:tenantA
ORDER BY created_at DESC LIMIT 1;
-- EXPECT: "cross_tenant_attempt"
```

---

## § Gherkin → Spec Mapping

| Scenario | Spec file | Test name | Grader type |
|---|---|---|---|
| SC-1 | `regression/.../staff-crear-happy.spec.ts` | "crea doctor, navega a workspace, agrega bloque semanal con fecha-fin" | e2e + state_check |
| SC-1b | `regression/.../staff-crear-happy.spec.ts` | "crea bloque quincenal con 6 iteraciones" | e2e + state_check |
| SC-1c | `regression/.../staff-week-nav-oneoff.spec.ts` | "navega a semana siguiente, agrega bloque puntual" | e2e + state_check |
| SC-1d | `regression/.../staff-week-nav-oneoff.spec.ts` | "elimina bloque sin citas, future slots retirados" | e2e + state_check |
| SC-2 | `regression/.../staff-credencial-invalida.spec.ts` | "ingresa credencial abc (no numérica)..." | e2e + visual_state |
| SC-3 | `regression/.../staff-crear-happy.spec.ts` + `shell-organism/staff-deactivate.spec.ts` | "toggle activo → off, citas futuras preservadas" | e2e + state_check |
| SC-3b | `shell-organism/staff-delete-block-preserve.spec.ts` | "UI advierte N citas confirmadas, confirmar elimina bloque" | e2e + state_check |
| SC-4 | `shell-organism/staff-cross-tenant-adversarial.spec.ts` | "tenant A intenta ver doctor de tenant B → 404 + audit" | e2e adversarial + state_check |
| SC-5 | backend integration only (test_doctor_dni_race.py) | — | integration |
| SC-6 | `regression/.../staff-crear-happy.spec.ts` | "tenant A ve exactamente sus 3 doctores, cero leak tenant B" | e2e + integration |
| SC-7 | `regression/.../staff-network-failure.spec.ts` | "muestra error banner + Reintentar, recover on retry" | e2e (page.route 503) |
| SC-8 | `regression/.../staff-network-failure.spec.ts` + `shell-organism/staff-empty.spec.ts` | "empty-state illustration + CTA" | e2e + axe |
| SC-9 | `regression/.../staff-network-failure.spec.ts` + `shell-organism/staff-large-dataset.spec.ts` | "pagination 24/page <500ms" | e2e + integration |
| SC-10 | `shell-organism/staff-empty.spec.ts` | "focus trap + Escape + Arrow nav + axe wcag2aa" | e2e keyboard + axe |
| SC-11 | `regression/.../staff-i18n-credencial.spec.ts` | "label por país (PE/AR/MX/CL) + neutro + currency" | e2e multi-locale |

**Visual goldens (defined, not yet generated):**
| Golden | Spec | Status |
|---|---|---|
| `staff/directorio-light.png` | `shell-organism/staff-large-dataset.spec.ts` | PENDING-STACK |
| `staff/directorio-dark.png` | idem | PENDING-STACK |
| `staff/perfil-light.png` | idem | PENDING-STACK |
| `staff/perfil-dark.png` | idem | PENDING-STACK |
| `staff/horarios-light.png` | idem | PENDING-STACK |
| `staff/horarios-dark.png` | idem | PENDING-STACK |
| `staff/servicios-pendiente-light.png` | idem | PENDING-STACK |

---

## § What's Verified-for-Real vs Static-Only-Now

| What | Verified-for-real (WHEN live) | Static-only now |
|---|---|---|
| Spec syntax, types, imports | tsc 0 errors, eslint 0 errors | Yes |
| Spec discovery | playwright --list: 41 specs found | Yes |
| SC-1..SC-11 gherkin coverage | All scenarios have spec coverage | Yes (spec written) |
| Happy-path writes (POST/PATCH/DELETE) | NO backend mock for writes — will hit BE:8002 | PENDING-STACK |
| State_check DB queries | Documented in grader comments per spec | PENDING-STACK |
| axe wcag2aa scan | axe-core/playwright installed, scoped assertions written | PENDING-STACK |
| Visual golden baselines | `toHaveScreenshot()` calls written, maxDiffPixelRatio: 0.001 | PENDING-STACK |
| Network failure recovery (SC-7) | page.route 503 is legitimate mock (tests UI behavior) | Will pass statically once FE up |
| Focus trap + keyboard nav (SC-10) | Written correctly | PENDING-STACK |

---

## § Files Delivered

| File | Type | Status |
|---|---|---|
| `e2e/fixtures/vitalia-fase2-lisa-doctores.fixture.ts` | Fixture (Clerk auth + mocks) | NEW |
| `e2e/pages/StaffDirectoryPage.ts` | POM | NEW |
| `e2e/pages/DoctorWorkspacePage.ts` | POM | PRE-EXISTING (T-FE-2) |
| `e2e/pages/AvailabilityCalendarPage.ts` | POM | PRE-EXISTING (T-FE-3) |
| `e2e/regression/vitalia-fase2-lisa-doctores/staff-crear-happy.spec.ts` | Spec (SC-1, SC-1b, SC-3, SC-6) | NEW |
| `e2e/regression/vitalia-fase2-lisa-doctores/staff-week-nav-oneoff.spec.ts` | Spec (SC-1c, SC-1d) | NEW |
| `e2e/regression/vitalia-fase2-lisa-doctores/staff-credencial-invalida.spec.ts` | Spec (SC-2) | NEW |
| `e2e/regression/vitalia-fase2-lisa-doctores/staff-network-failure.spec.ts` | Spec (SC-7, SC-8, SC-9) | NEW |
| `e2e/regression/vitalia-fase2-lisa-doctores/staff-i18n-credencial.spec.ts` | Spec (SC-11) | NEW |
| `e2e/shell-organism/staff-cross-tenant-adversarial.spec.ts` | Spec (SC-4) | NEW |
| `e2e/shell-organism/staff-deactivate.spec.ts` | Spec (SC-3 deep) | NEW |
| `e2e/shell-organism/staff-delete-block-preserve.spec.ts` | Spec (SC-3b) | NEW |
| `e2e/shell-organism/staff-empty.spec.ts` | Spec (SC-8, SC-10 axe) | NEW |
| `e2e/shell-organism/staff-large-dataset.spec.ts` | Spec (SC-9, V-VIS-1..4) | NEW |
| `playwright.config.ts` | Config (added shell-organism/staff-* to smoke testMatch) | MODIFIED |
| `docs/product/stories/.../06-tickets.yaml` | T-E2E state: specs-written | MODIFIED |

---

## § Static Gate Results

| Gate | Result | Detail |
|---|---|---|
| `tsc --noEmit` | PASS (0 errors) | All spec/POM/fixture files type-correct |
| `eslint e2e/...` | PASS (0 errors, 0 warnings) | All new files clean |
| `playwright --list` | PASS | 41 tests discovered (19 regression + 22 shell-organism) |
| Live run | PENDING-STACK | BE:8002 + FE:3002 DOWN — zustand pre-existing bug |

---

## § Non-Egoismo Clause Applied

Per `04-validators.yaml § non_egoismo_clause`: the pre-existing zustand workspace resolution bug in `vitalia/docs/observed-bugs/2026-05-31-zustand-workspace-resolution-luana-hooks.md` was NOT fixed in this ticket (out of scope). It was documented and flagged. This story only touches `e2e/regression/vitalia-fase2-lisa-doctores/` + `e2e/shell-organism/staff-*.spec.ts` + `e2e/pages/StaffDirectoryPage.ts` + `e2e/fixtures/vitalia-fase2-lisa-doctores.fixture.ts` + playwright.config.ts (testMatch addition only).
