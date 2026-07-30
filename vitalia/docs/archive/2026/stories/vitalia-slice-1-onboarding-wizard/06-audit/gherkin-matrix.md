# Phase D — Gherkin verification matrix

> Story: `vitalia-slice-1-onboarding-wizard`
> Brand: `vitalia`
> Auditor: `/auditor` (Conv 3 Phase D)
> Date: 2026-05-18
> SSoT scenarios: `vitalia/docs/product/stories/vitalia-ux-discovery/01-spec.md` § Wizard Brand Studio (Batch 7 ratificado 2026-05-17) + `02-design-agentic.md` (referenced via 06-tickets.yaml ticket gherkin_coverage)
> Goldens shipped: `vitalia/backend/tests/agentic_evals/copilot/wizard_goldens/{happy,negative,edge_browser_close,adversarial}.yaml` + runner `test_wizard_pass_k_evaluation.py` (k=3 threshold 0.5)

## Matrix

| ID | Scenario (Gherkin description) | Test path | Status |
|---|---|---|---|
| SC-W1 | Happy path — usuario inicia wizard, Valeria extrae contexto desde URL, confirma slots required (name + vertical + location), simulate Adrián preview, complete → tenant.is_onboarded=True | `vitalia/backend/tests/agentic_evals/copilot/wizard_goldens/happy.yaml` (via `test_wizard_pass_k_evaluation.py::test_happy_pass_k`) | ✅ PASS (k=3, ≥0.5 threshold, included in T-7 smoke regression 74ca79a) |
| SC-W2 | Incomplete input — usuario provee solo `name`, Valeria re-prompts por `vertical` y `location`, eventual save_draft con slots_pending | `vitalia/backend/tests/agentic_evals/copilot/wizard_goldens/negative.yaml` (via `test_wizard_pass_k_evaluation.py::test_negative_pass_k`) | ✅ PASS (k=3, T-7 regression verified) |
| SC-W3 | Browser close + resume — usuario cierra pestaña mid-wizard, re-login, wizard resume desde último slot confirmado vía AsyncPostgresSaver checkpointer | `vitalia/backend/tests/agentic_evals/copilot/wizard_goldens/edge_browser_close.yaml` (via `test_wizard_pass_k_evaluation.py::test_edge_browser_close_pass_k`) + `vitalia/backend/tests/integration/copilot/test_wizard_onboarding_graph_e2e.py::test_checkpointer_state_resume` | ✅ PASS (k=3 + integration test 5/5 GREEN, T-5 69049df + T-7 74ca79a) |
| SC-W4 | PII + XSS safety — usuario submitea URL con PII/script malicioso, sanitize_payload bloquea PHI en trace + voice sample rechaza unsafe content | `vitalia/backend/tests/agentic_evals/copilot/wizard_goldens/adversarial.yaml` (via `test_wizard_pass_k_evaluation.py::test_adversarial_pass_k`) | ✅ PASS (k=3 threshold 0.5, T-7 smoke regression verified) |
| SC-BE-1 | BE — repository tenant isolation: cross-tenant query returns None (NOT 403 — repo layer) | `vitalia/backend/tests/modules/vitalia/copilot/infrastructure/repositories/test_onboarding_progress_repository.py::test_get_by_tenant_user_cross_tenant_returns_none` + `test_brand_studio_draft_repository.py::test_get_by_id_tenant_cross_tenant_returns_none` | ✅ PASS (T-1 135ffe0, 27/27 unit) |
| SC-BE-2 | BE — routes DI real (AsyncMock removed): 7 wizard endpoints respond 200 con response_model coherente | `vitalia/backend/tests/modules/vitalia/copilot/api/routes/test_wizard_onboarding_routes.py` (9 route tests) | ✅ PASS (T-3 13d0a0b, 9/9 route tests) |
| SC-BE-3 | BE — LivePreviewService cache + throttle integration | `vitalia/backend/tests/modules/vitalia/copilot/application/services/test_live_preview_service.py` (4 tests happy+cached+no-draft+landing-snippet) | ✅ PASS (T-2 7039d69) |
| SC-AGENTIC-1 | Agentic — 4 Valeria tools registered via EP-3 con @tool decorator + tenant_id mandatory | `vitalia/backend/tests/modules/vitalia/copilot/tools/test_wizard_tools_wiring.py` (6 tests) | ✅ PASS (T-4 615a252) |
| SC-AGENTIC-2 | Agentic — cost canonicalization regression (pop_cost(litellm_call_id) returns non-None Decimal post PI-12 S1 T-1 fix) | `vitalia/backend/tests/modules/vitalia/copilot/tools/test_wizard_tools_wiring.py::test_cost_canonicalization_regression` | ✅ PASS (T-4 615a252) |
| SC-AGENTIC-3 | Agentic — LangGraph supervisor end-to-end con max-iter 25 guard + cache hit rate iter 2+ + cost budget ≤$0.10 USD/session | `vitalia/backend/tests/integration/copilot/test_wizard_onboarding_graph_e2e.py` (5 integration tests) | ✅ PASS (T-5 69049df, 5/5 integration) |
| SC-FE-1 | FE — wizard 9 components + 6 hooks renderizan correctamente con design tokens semánticos (no hex hardcoded) | `vitalia/frontend/src/features/onboarding/__tests__/components/` (4 component test files) + `__tests__/hooks/` (3 hook test files) | ✅ PASS (T-6 221d0ef, 54/54 onboarding, 299/299 full suite) |
| SC-FE-2 | FE — Spanish neutro tuteo en `config/copy.ts` (no voseo) | `grep -rE "\bsos\b\|\btenés\b\|\bpodés\b\|..." src/features/onboarding/config/copy.ts` | ✅ PASS (T-6 221d0ef, 0 voseo verbs hook clean) |
| SC-FE-3 | FE — Audio mode disabled tooltip "Disponible próximamente" en `ModeSelector` (Slice 2 deferred per OQ-3) | `vitalia/frontend/src/features/onboarding/__tests__/components/ModeSelector.test.tsx` | ✅ PASS (T-6 221d0ef) |
| SC-FE-4 | FE — Smoke E2E spec existe en `e2e/specs/vitalia/wizard-onboarding.smoke.spec.ts` + POM | filesystem check: `vitalia/frontend/e2e/specs/vitalia/wizard-onboarding.smoke.spec.ts` + `vitalia/frontend/e2e/pages/wizard-onboarding.page.ts` | ✅ PASS (T-6 221d0ef — spec written; live run in Phase E) |

## Aggregate

- **Scenarios covered:** 13/13 (4 Gherkin SC-W1..W4 from spec + 9 derived per ticket acceptance criteria)
- **All PASS:** 13/13
- **NO COVERAGE flags:** 0
- **FAIL flags:** 0

## Verdict Phase D

✅ **PASS** — Phase D complete. All Gherkin scenarios + per-ticket acceptance criteria covered by passing tests. Proceed to Phase E (Playwright E2E live).

## Notes

- Story transitioned `developing → developed` on 2026-05-18, post-cement-date of story-closure-gate. Full Phase D enforcement applied.
- `06-tickets-refresh.yaml` does NOT contain explicit `gherkin_coverage` field per ticket (inherited package from parent `vitalia-ux-discovery/06-tickets.yaml`). However, each ticket's `acceptance.test_paths` + the 4 wizard goldens YAML provide equivalent traceability.
- Phase E will validate SC-W1..W4 E2E con Playwright contra dev stack vivo (port 3002).
