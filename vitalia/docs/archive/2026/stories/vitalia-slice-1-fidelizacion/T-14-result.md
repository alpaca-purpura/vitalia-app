# T-14 — E2E Playwright POM + smoke + 4 regression specs (RESULT)

**Status:** files-staged-but-runtime-deferred
**Commit:** 119d4fc
**Branch:** wip/vitalia
**Closed by:** orchestrator manual (agent token cap interrupted mid-task)

## Scope shipped

8 files, 2042 LOC (`git show --stat 119d4fc`):

| File | LOC | Purpose |
|---|---|---|
| `vitalia/frontend/e2e/pages/fidelizacion.page.ts` | 382 | POM canonical |
| `vitalia/frontend/e2e/fixtures/clinic-context.fixture.ts` | 166 | tenant + clinic context multi-tenant |
| `vitalia/frontend/e2e/fixtures/fidelizacion-seed.fixture.ts` | 418 | DB seed + tear-down |
| `vitalia/frontend/e2e/specs/smoke/fidelizacion.smoke.spec.ts` | 213 | mount + 5 tabs + KPIs + axe-core a11y |
| `vitalia/frontend/e2e/specs/regression/fidelizacion-multi-session-happy.spec.ts` | 135 | SC-01 |
| `vitalia/frontend/e2e/specs/regression/fidelizacion-absence-no-optin.spec.ts` | 186 | SC-02 |
| `vitalia/frontend/e2e/specs/regression/fidelizacion-follow-up-doctor-vencido.spec.ts` | 219 | SC-03 |
| `vitalia/frontend/e2e/specs/regression/fidelizacion-adversarial.spec.ts` | 323 | SC-04 |

## Static validation (build-time)

| Validator | Result |
|---|---|
| `tsc --noEmit` (all FE) | EXIT 0 ✅ |
| `eslint` (T-14 files) | EXIT 0 ✅ |
| `eslint` (full e2e/) | 43 errors in OTHER specs (NOT T-14 scope) — pre-existing |
| FE arch fitness (38 tests) | unchanged GREEN ✅ |

## Live Playwright run — DEFERRED to Step 3

The builder agent ran out of context tokens mid-task while attempting to
update cross-tenant guards in `aurora-dental-ar.fixture.ts` /
`mindful-psych-cl.fixture.ts` / `sanare-latam-mx.fixture.ts` — EXISTING
fixtures that are NOT in T-14 scope per `06-tickets.yaml::files_in_scope`.

Orchestrator finalized commit with EXACT T-14 scope, leaving those
existing fixtures intact (git-safety hard rule).

Live Playwright execution requires `make dev-vitalia` stack up (port 3002)
+ fresh storageState (`vitalia/frontend/playwright/.clerk/user.json`).
Will run during **Step 3 pre-auditor validation suite** with full inbox +
fidelizacion stack integrated.

## Gherkin coverage matrix

| Scenario (Gherkin) | Test path | Static status |
|---|---|---|
| SC-01 Happy multi-session | `e2e/specs/regression/fidelizacion-multi-session-happy.spec.ts::scenario-01` | ✅ COMPILES |
| SC-02 Absence no opt-in | `e2e/specs/regression/fidelizacion-absence-no-optin.spec.ts::scenario-02` | ✅ COMPILES |
| SC-03 Follow-up doctor vencido | `e2e/specs/regression/fidelizacion-follow-up-doctor-vencido.spec.ts::scenario-03` | ✅ COMPILES |
| SC-04 Adversarial | `e2e/specs/regression/fidelizacion-adversarial.spec.ts::scenario-04` | ✅ COMPILES |

## Handoff to auditor (Phase D)

Auditor must run Playwright live during Phase D verification:

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke e2e/specs/smoke/fidelizacion.smoke.spec.ts e2e/specs/regression/
```

If runtime fails due to cross-tenant guard env var (`E2E_CLERK_ORG_ID`)
the auditor should escalate to dev-team for guard fix (small surface,
likely 1-2 line patch in `auth.fixture.ts`).
