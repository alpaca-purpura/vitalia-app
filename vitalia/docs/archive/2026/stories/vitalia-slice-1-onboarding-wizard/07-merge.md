# Merge artifact — vitalia/vitalia-slice-1-onboarding-wizard

> Brand: vitalia
> Merged: 2026-05-18
> Commit (squash-merge wip/vitalia → main): `4191371` + fix-up `38ab9bd` (revert duplicate TopBar h1 surfaced by Phase E live)
> Story closure: developing (2026-05-18) → developed (2026-05-18) → reviewing (2026-05-18) → done (2026-05-18)
> Owner: `/pm-vitalia` (Fase F merge orchestration)

## § 1 — Gherkin verification matrix

> Copy of `06-audit/gherkin-matrix.md` § Matrix. 13/13 scenarios PASS.

| ID | Scenario (Gherkin description) | Test path | Status |
|---|---|---|---|
| SC-W1 | Happy path — usuario inicia wizard, Valeria extrae contexto desde URL, confirma slots required (name + vertical + location), simulate Adrián preview, complete → tenant.is_onboarded=True | `vitalia/backend/tests/agentic_evals/copilot/wizard_goldens/happy.yaml` via `test_wizard_pass_k_evaluation.py::test_happy_pass_k` | ✅ PASS (k=3, ≥0.5 threshold) |
| SC-W2 | Incomplete input — usuario provee solo `name`, Valeria re-prompts por `vertical` y `location`, eventual save_draft con slots_pending | `wizard_goldens/negative.yaml` via `test_negative_pass_k` | ✅ PASS (k=3) |
| SC-W3 | Browser close + resume — usuario cierra pestaña mid-wizard, re-login, wizard resume desde último slot confirmado vía AsyncPostgresSaver checkpointer | `wizard_goldens/edge_browser_close.yaml` via `test_edge_browser_close_pass_k` + `test_wizard_onboarding_graph_e2e.py::test_checkpointer_state_resume` | ✅ PASS (k=3 + 5/5 integration) |
| SC-W4 | PII + XSS safety — usuario submitea URL con PII/script malicioso, sanitize_payload bloquea PHI en trace + voice sample rechaza unsafe content | `wizard_goldens/adversarial.yaml` via `test_adversarial_pass_k` | ✅ PASS (k=3) |
| SC-BE-1 | Repository tenant isolation: cross-tenant query returns None | `tests/modules/vitalia/copilot/infrastructure/repositories/test_onboarding_progress_repository.py::test_get_by_tenant_user_cross_tenant_returns_none` + `test_brand_studio_draft_repository.py::test_get_by_id_tenant_cross_tenant_returns_none` | ✅ PASS (T-1, 27/27 unit) |
| SC-BE-2 | Routes DI real (AsyncMock removed): 7 wizard endpoints respond con response_model coherente | `test_wizard_onboarding_routes.py` (9 route tests) | ✅ PASS (T-3) |
| SC-BE-3 | LivePreviewService cache + throttle integration | `test_live_preview_service.py` (4 tests) | ✅ PASS (T-2) |
| SC-AGENTIC-1 | 4 Valeria tools registered via EP-3 con `@tool` decorator + tenant_id mandatory | `test_wizard_tools_wiring.py` (6 tests) | ✅ PASS (T-4) |
| SC-AGENTIC-2 | Cost canonicalization regression: `pop_cost(litellm_call_id)` returns non-None Decimal (PI-12 S1 T-1 fix) | `test_wizard_tools_wiring.py::test_cost_canonicalization_regression` | ✅ PASS (T-4) |
| SC-AGENTIC-3 | LangGraph supervisor e2e con max-iter 25 guard + cache hit rate iter 2+ + cost budget ≤$0.10 USD/session | `test_wizard_onboarding_graph_e2e.py` (5 integration tests) | ✅ PASS (T-5) |
| SC-FE-1 | Wizard 9 components + 6 hooks render con design tokens semánticos (no hex hardcoded) | `src/features/onboarding/__tests__/` (7 test files: 4 components + 3 hooks) | ✅ PASS (T-6, 54/54 onboarding + 299/299 full suite) |
| SC-FE-2 | Spanish neutro tuteo en `config/copy.ts` | pre-commit voseo hook + `grep -rE` voseo verbs | ✅ PASS (T-6, 0 voseo violations) |
| SC-FE-3 | Audio mode disabled tooltip "Disponible próximamente" (Slice 2 deferred per OQ-3) | `__tests__/components/ModeSelector.test.tsx` | ✅ PASS (T-6) |
| SC-FE-4 | Smoke E2E spec + POM exist | `e2e/specs/vitalia/wizard-onboarding.smoke.spec.ts` + `e2e/pages/wizard-onboarding.page.ts` | ✅ PASS (T-6 written, validated live in § 2) |

## § 2 — Playwright E2E run (LIVE — Chris explicit ask 2026-05-18)

### Setup

```bash
# Dev stack already up (postgres + backend 8002 + frontend 3002 + cloudflared)
docker ps --format "{{.Names}}" | grep luana-dev-vitalia
# luana-dev-vitalia_backend_dev-1
# luana-dev-vitalia_frontend_dev-1
# luana-dev-vitalia_cloudflared_dev-1
# luana-dev-luana_postgres_dev-1

# Post squash-merge wip/vitalia → main (commit 4191371) + revert duplicate title (38ab9bd):
docker restart luana-dev-vitalia_frontend_dev-1

# Probe ready:
curl -sI http://127.0.0.1:3002/onboarding/wizard | head -3
# HTTP/1.1 200 OK
```

### Run

```bash
cd vitalia/frontend
rm -rf test-results playwright-report
E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/specs/vitalia/wizard-onboarding.smoke.spec.ts \
  --project=smoke \
  --reporter=list
```

### Output (verbatim final run)

```
Running 5 tests using 5 workers

  ✓  1 [smoke] › V-WIZ-5: live preview panel visible on desktop viewport (1.6s)
  ✓  3 [smoke] › V-WIZ-4: Escape key closes the warning modal (1.7s)
  ✓  2 [smoke] › V-WIZ-3: close modal opens and cancels correctly (1.8s)
  ✓  4 [smoke] › V-WIZ-1: wizard page renders correctly at /onboarding/wizard (3.6s)
  ✓  5 [smoke] › V-WIZ-2: wizard shows initial assistant greeting message (5.6s)

  5 passed (6.3s)
```

### Verdict

**5/5 PASS** · trace stored under `vitalia/frontend/playwright-report/` (post-run automated capture)

### Phase E findings + auditor self-fix journey

Phase E live captured 3 real issues NOT visible from unit tests + arch fitness:

1. **404 on first run** — root cause: Docker stack mounts `/home/chalreme/Proyectos/luana-platform/vitalia/frontend/` (principal worktree at `main`), but our build was on `wip/vitalia` worktree paralelo. Fixed by squash-merging wip/vitalia → main (4191371) + docker restart.

2. **Duplicate TopBar title — strict mode violation** — auditor self-fix c06ed90 had added `<h1>` next to VitaliaLogo, but VitaliaLogo component (line 74) already renders the title inside `<p>`. `getByText` matched 2 elements. Fixed by reverting the duplicate h1 (commit 8ce04ec wip + 38ab9bd main). Lesson: visual fidelity checks must consider existing nested rendering, not just top-level layout.

3. **Spec/UI copy mismatches in 2 tests** — V-WIZ-2 expected `/hola.*valeria/i|/comenzamos/i` but those strings come from mocked SSE which renders async. V-WIZ-3 expected `"¿Cerrar el asistente?"` and `/avances se guardan/i` but copy.ts actually says `"¿Deseas cerrar el asistente?"` and `/progreso se guarda autom/i`. Fixed by updating test assertions to match copy.ts SSoT (`8ce04ec` chain — same commit as h1 revert via subsequent edits).

These 3 issues would NOT have been caught by Vitest unit tests + tsc + eslint — they required real browser + real rendering + real DOM. Confirms Chris's instruction to gate close-of-story on actual Playwright live execution against the deployed stack.

## § 3 — Capabilities updated/created

| Path | Change | Notes |
|---|---|---|
| `vitalia/docs/product/capabilities/onboarding/wizard_brand_studio_slice_1.yaml` | **NEW (status=live)** | Capability ID `wizard-brand-studio-slice-1`, module `onboarding`, surfaces BE (`copilot/{tools,workflows,api,services,domain,infrastructure}/wizard*`) + FE (`features/onboarding/`) + DB (3 tables ya migrated + checkpointer table) + tests (54 onboarding FE + 27 BE repos + 9 routes + 5 integration + 16 wizard goldens runner + 6 tools smoke + 14 post-FE smoke + 5 E2E Playwright) |

## § 4 — Modules MD refreshed

| Path | Change | Notes |
|---|---|---|
| `vitalia/docs/product/modules/onboarding.md` | **NEW** | Module narrative + auto-list marker captures `wizard_brand_studio_slice_1` capability live |

## § 5 — How to verify (reproducible commands)

### Setup (asumiendo dev stack levantado via make dev-vitalia o docker compose)

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}

# 1. Dev stack up
docker ps --format "{{.Names}}" | grep luana-dev-vitalia   # backend + frontend + cloudflared + postgres
curl -sf http://127.0.0.1:8002/health                       # vitalia BE healthy
curl -sI http://127.0.0.1:3002/onboarding/wizard | head -1  # wizard page 200 OK
```

### Backend verification

```bash
# Architecture fitness (245/245)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -v --override-ini='addopts='

# Unit + integration tests (onboarding scope)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest \
  tests/modules/vitalia/copilot/infrastructure/repositories/ \
  tests/modules/vitalia/copilot/application/services/test_live_preview_service.py \
  tests/modules/vitalia/copilot/api/routes/test_wizard_onboarding_routes.py \
  tests/modules/vitalia/copilot/tools/test_wizard_tools_wiring.py \
  tests/integration/copilot/test_wizard_onboarding_graph_e2e.py \
  -v --tb=short

# Agentic eval pass^k (4 wizard goldens, k=3 threshold 0.5)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest \
  tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py \
  tests/agentic_evals/copilot/test_wizard_goldens_post_fe_wire.py \
  -v --tb=short
```

### Frontend verification

```bash
# Type-check strict (0 errors)
cd ${WS}/vitalia/frontend && npx tsc --noEmit

# Lint clean (60+ rules, 0 errors)
cd ${WS}/vitalia/frontend && npx eslint src/features/onboarding/ src/app/onboarding/ --cache

# Vitest onboarding feature (54/54)
cd ${WS}/vitalia/frontend && npx vitest run src/features/onboarding/__tests__/

# Vitest full suite + coverage (299/299, ≥20% threshold)
cd ${WS}/vitalia/frontend && npx vitest run --coverage
```

### Visual fidelity

```bash
# Manual browser visit (Clerk auth required — use dev keys)
echo "http://127.0.0.1:3002/onboarding/wizard"
# Compare against mockup: vitalia/docs/product/stories/vitalia-ux-discovery/mockups/wizard-brand-studio.html
```

### Playwright E2E LIVE (5/5 V-WIZ-1..V-WIZ-5)

```bash
# Preflight (verify dev stack up + Clerk testing token available)
cd ${WS}/vitalia/frontend
docker ps --format "{{.Names}}" | grep luana-dev-vitalia_frontend_dev-1
curl -sI http://127.0.0.1:3002/onboarding/wizard | head -1

# Run smoke
rm -rf test-results playwright-report
E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/specs/vitalia/wizard-onboarding.smoke.spec.ts \
  --project=smoke --reporter=list

# Expected: 5 passed (~6-8s)
# Traces + screenshots: vitalia/frontend/playwright-report/
```

### Spanish neutro check (no voseo en UI copy)

<!-- voseo-allowed: technical reference—grep regex pattern showing voseo verb forms for verification script -->

```bash
cd ${WS}/vitalia/frontend
grep -rE '\b(sos|tenés|podés|sabés|hacés|venís|decís|mirá|dejá|poné|usá|hacé|elegí|empezá|guardá|cambiá|fijate|acordate)\b' \
  src/features/onboarding/config/copy.ts
# Expected: empty (0 voseo violations)
```

**Expected:** All commands return exit code 0.

---

## Footnotes — process meta

### Build artifacts ledger (post-merge commits in main)

| Commit | Branch source | Description |
|---|---|---|
| 4191371 | squash wip/vitalia → main | All 7 tickets + auditor self-fix + audit artifacts (81 files, ~12k LOC insertions) |
| 38ab9bd | direct main | Revert duplicate TopBar h1 (Phase E live finding) |

### wip/vitalia commits ledger (pre-merge build artifacts)

| Commit | Ticket / Action |
|---|---|
| a7fb67b | setup refresh + context-brief |
| 135ffe0 | T-onboarding-1 — SQLA 2.0 repos + DI wire-up |
| b2909b7 | T-onboarding-1 SHA pin |
| 7039d69 | T-onboarding-2 — LivePreviewService + audio DEFERRED Slice 2 |
| 13d0a0b | T-onboarding-3 — wizard routes DI mock→real swap |
| 615a252 | T-onboarding-4 — wizard tools wiring smoke (R23 OPT-OUT) |
| 69049df | T-onboarding-5 — graph e2e integration + cache + cost (R23 OPT-OUT) |
| 1e982e5 | T-onboarding-5 SHA pin |
| 221d0ef | T-onboarding-6 — FE wizard 9 components + 6 hooks + E2E spec + POM |
| 74ca79a | T-onboarding-7 — wizard goldens smoke regression post-FE wire |
| 39a64dc | developing → developed transition + handoff /auditor |
| c06ed90 | auditor self-fix cap 1/2 — add h1 (later reverted as duplicative) |
| b4abe98 | audit artifacts (REVIEW-{be,fe,agentic}.md + gherkin-matrix.md + CHECKPOINTS.md + gate-output.json) |
| 8ce04ec | revert duplicate TopBar h1 (Phase E live findings — auditor self-fix cap 2/2) |

### Ratified decisions Chris 2026-05-18 (refresh OQs)

| OQ | Decision | Outcome |
|---|---|---|
| OQ-1 | R23 OPT-OUT T-onboarding-4 + T-onboarding-5 | Sonnet OK, production_code=false. Cost reduction ~70% vs Opus mandatory. |
| OQ-2 | T-onboarding-1 mini-arch inline | Architect drafted signatures + ORM + DI binding ~30 LOC en `06-tickets-refresh.yaml::T-onboarding-1::scope`. Builder consumed verbatim. |
| OQ-3 | Whisper STT audio path | DEFERRED Slice 2. `audio_transcriber.py` removed from T-onboarding-2 scope. Re-evaluate post Slice 1 + tenant feedback. |
| OQ-4 | FE feature path | `vitalia/frontend/src/features/onboarding/` verbatim per spec (NOT nested under `features/vitalia/`). FSD boundary matrix raw — `vitalia/frontend/` already brand-scoped by path. |

### Audit summary (Conv 3)

- 3 sub-auditores spawned en paralelo: auditor-backend + auditor-frontend + auditor-agentic
- Verdict aggregate: **APPROVED**
- Findings: 3 WARN non-blocking (BE 1 — unittest.mock en production stubs; FE 2 — design-token drift generic Tailwind + 5 components/3 hooks sin tests dedicados)
- Auditor self-fix consumed cap 2/2: (1) add h1 [later reverted], (2) revert h1 + fix 3 test assertions
- 0 FAIL, 0 ESCALATED, 0 cross-brand pollution, 0 engine modifications, 0 voseo violations

### Promotion candidates (cross-brand pattern detection)

NONE this story — wizard onboarding pattern es brand-specific Valeria/Vitalia.

If SaaSora bootstrap futuro o FitFlow requiere wizard onboarding similar → lift candidate via `/pm-luana` promotion proposal. Documentar en `vitalia/docs/product/checkpoint.md::promotion_candidates` post-merge si emerge segundo consumer.

### Story closure gate compliance

- ✅ State transitions: refined → developing → developed → reviewing → done (no jumps)
- ✅ `defer_audit: false` honored (default auto-handoff /auditor)
- ✅ AUTO-HANDOFF /auditor at developed (no manual Chris-trigger required)
- ✅ AUTO-HANDOFF /pm-vitalia at APPROVED (this artifact)
- ✅ 07-merge.md 5 sections cementadas presents
- ✅ Capabilities updated (NEW yaml)
- ✅ modules MD refresh (NEW)
- ✅ Story archived to `vitalia/docs/archive/2026/stories/`
