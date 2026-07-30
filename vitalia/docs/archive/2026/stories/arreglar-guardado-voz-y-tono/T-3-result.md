# T-3-result.md — E2E Playwright voz-y-tono autosave (real-backend) + a11y

**Story:** arreglar-guardado-voz-y-tono  
**Ticket:** T-3  
**Surface:** FE (E2E + unit test extension)  
**Branch:** wip/vitalia  
**Date:** 2026-05-30  

---

## § Deliverables created

| # | File | Status |
|---|---|---|
| 1 | `vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/poms/voz-tono-section.pom.ts` | CREATED |
| 2 | `vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/voz-arquetipo-autosave.spec.ts` | CREATED |
| 3 | `vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/voz-bloque-autosave.spec.ts` | CREATED |
| 4 | `vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/voz-autosave-error.spec.ts` | CREATED |
| 5 | `vitalia/frontend/e2e/a11y/arreglar-guardado-voz-y-tono.spec.ts` | CREATED |
| 6 | `vitalia/frontend/src/features/lisa/hooks/__tests__/usePersonalityAutosave.test.ts` | EXTENDED (3 new camelCase payload tests) |

---

## § Validator results

### fe_typecheck — PASS
```
cd vitalia/frontend && npx tsc --noEmit
(exit code 0 — no output = no errors)
```

### Vitest — usePersonalityAutosave.test.ts — PASS (13/13)
```
✓ src/features/lisa/hooks/__tests__/usePersonalityAutosave.test.ts (13 tests) 189ms

Test Files  1 passed (1)
     Tests  13 passed (13)
  Start at  17:40:23
  Duration  1.03s
```
New camelCase payload tests added (3):
- `scheduleAutosave envía payload camelCase (soISpeak, no so_i_speak)` ✓
- `scheduleAutosave con solo archetype: payload contiene 'archetype'` ✓
- `payload combinado archetype + soISpeak contiene ambos en camelCase` ✓

---

## § E2E execution results

### Infrastructure blocker (honest reporting per test-design-doctrine.md § Verificación REAL)

**Blocker:** The test tenant (`VITALIA_PE_TENANT_ID = clinica-salud-vitalia-pe-test`) does not have
the `lisa/marca/voz-y-tono` sub-sub-tab accessible in the dev stack.

**Evidence (screenshot):** When navigating to `/{tenantId}/lisa/marca/voz-y-tono`, the shell renders but
the panel-content shows: *"No encontramos esta vista — Quizás el enlace está roto o el agente que buscas no existe en esta clínica."*

**Auth IS working:** The shell loads (Valeria, agents ribbon visible), Clerk storage state is valid
(~365 days remaining). The issue is purely that the test tenant lacks the voz-y-tono sub-sub-tab
seeded/configured in the dev DB.

**Commands attempted:**
```bash
cd vitalia/frontend

# Error spec (mocked PATCH 503)
E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/regression/arreglar-guardado-voz-y-tono/voz-autosave-error.spec.ts --project=smoke
# Result: 2 passed (tests that don't require waitForLoaded), 3 failed (timeout on archetype-selector)

# A11y spec
E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/a11y/arreglar-guardado-voz-y-tono.spec.ts --project=a11y
# Result: 2 passed, 6 failed (same root cause)
```

**Root cause analysis:** The `waitForLoaded()` and `waitForVozTonoInteractive()` helpers timeout because
neither `[data-testid="lisa-marca-content"]` nor `[data-testid="archetype-selector"]` appear in the DOM —
the route resolves to the "No encontramos esta vista" empty state. This is a seed/config issue in the
dev environment, not a bug in the spec files.

### Commands to run once blocker is resolved
```bash
cd vitalia/frontend

# All 4 specs together
E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/regression/arreglar-guardado-voz-y-tono/ \
  e2e/a11y/arreglar-guardado-voz-y-tono.spec.ts \
  --project=smoke

# a11y specifically
E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/a11y/arreglar-guardado-voz-y-tono.spec.ts \
  --project=a11y
```

### What "resolving the blocker" means
1. Ensure test tenant `clinica-salud-vitalia-pe-test` (or `VITALIA_PE_TENANT_ID` env var points to one)
   has personality seeded with `archetype='caregiver'` and the 6 voice blocks populated.
2. Confirm route `/{tenantId}/lisa/marca/voz-y-tono` renders the VozTonoView component (not empty state).
3. This may require: `make dev-vitalia` + `docker exec luana-vitalia-backend-dev alembic upgrade head`
   + seed script for the test tenant.

---

## § Skills consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `playwright-expert` | SSoT for Clerk auth lifecycle, POM patterns, network mocking, freshness gate | Used `setupClerkTestingToken` + storage state path matching identidad fixture pattern. Real backend for arquetipo/bloque specs; `page.route` mock ONLY for error spec (deliberate). |
| `frontend-expert` | FSD-Lite boundaries, component patterns, test patterns | Confirmed pattern mirrors `lisa-marca-identidad-autosave.spec.ts` fixture + POM structure. |
| `test-design-doctrine.md` | Verificación REAL ≠ HTTP 200 | Specs use real backend (no mock) for happy paths. Only error scenario uses mock (deliberately). camelCase payload tested in unit test to catch the 422 root cause at hook level. |
| `vitalia-design-system` | Shell organism tokens, agent routing | Confirmed route structure `/{tenantId}/lisa/marca/voz-y-tono` per ADR-vitalia-004 N3-static. |

---

## § Spec design decisions

### Why specs 2+3 use REAL backend (no page.route mock on PATCH)
Per `test-design-doctrine.md § Verificación REAL ≠ HTTP 200`:
- The bug shipped because the unit test mocked the API → false green.
- A mocked PATCH always returns 200 regardless of whether T-1 (sanitize_payload fix) and T-2
  (camelCase alias) are actually deployed.
- Only a real PATCH exercises the audit writer code path (T-1) and the DTO alias resolver (T-2).
- If PATCH returns 200 on the real backend → bug is fixed. If 500 → T-1 not applied. If 422 → T-2 not applied.

### Why spec 4 (error) uses page.route mock
The error scenario (`autosave-error-muestra-badge`) needs to test the FE error handling path. We cannot
reliably make the real backend return 503 on demand without infrastructure side effects. The mock is
**deliberate and documented** in the spec header. This is the single allowed mock per T-3 spec.

### POM design
`VozTonoSectionPom` is **new** (not reusing `VozTonoSectionPage` from `vitalia-fase2-lisa-marca/poms/`).
Rationale: the existing POM is scoped to the original story (F2-S7) with different methods (fillBlock,
getBlockValue by enum). The T-3 POM adds `goto()`, `reload()`, `editVoiceBlock(name, text)` where `name`
is the UI-facing block label, and `getAutosaveStatus()`. The two POMs serve different stories and different
test scenarios — no duplication (different contracts).

### camelCase payload unit test
The extension to `usePersonalityAutosave.test.ts` verifies the hook sends `soISpeak` (camelCase) not
`so_i_speak` (snake_case). This is the minimal unit-level guard against the 422 bug regressing at the
hook layer. The E2E specs verify end-to-end from UI action to HTTP 200.

---

## § Commit

> **To be committed after reviewing the files above.**
> Files scoped to this ticket only (per parallel-safety.md — single-hub shared index):

```
vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/poms/voz-tono-section.pom.ts
vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/voz-arquetipo-autosave.spec.ts
vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/voz-bloque-autosave.spec.ts
vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/voz-autosave-error.spec.ts
vitalia/frontend/e2e/a11y/arreglar-guardado-voz-y-tono.spec.ts
vitalia/frontend/src/features/lisa/hooks/__tests__/usePersonalityAutosave.test.ts
vitalia/docs/product/stories/arreglar-guardado-voz-y-tono/T-3-result.md (this file)
```

Commit message:
```
test(vitalia/lisa): E2E voz-y-tono autosave real-backend + a11y [T-3 arreglar-guardado-voz-y-tono]
```

---

## § Infra blocker escalation

<!-- @pm: T-3 specs are correctly written and TypeScript-clean. Vitest 13/13 PASS.
E2E blocked by missing seed: test tenant clinica-salud-vitalia-pe-test has no voz-y-tono sub-sub-tab
accessible (shell shows "No encontramos esta vista"). Needs: personality seed for test tenant +
confirm route /{tenantId}/lisa/marca/voz-y-tono renders VozTonoView. Once seeded, command to run:
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test
e2e/regression/arreglar-guardado-voz-y-tono/ e2e/a11y/arreglar-guardado-voz-y-tono.spec.ts --project=smoke
Honesty over false green (this story is literally about that). -->
