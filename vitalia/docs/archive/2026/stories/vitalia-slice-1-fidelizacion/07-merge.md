# Merge artifact — vitalia/vitalia-slice-1-fidelizacion

> Brand: vitalia
> Merged: 2026-05-20
> Commit (squash-merge): TBD (set post merge)
> Branch source: wip/vitalia (heads: 9b676ee + chain)
> Audit verdict: APPROVED iter 3 (BE, post F1+F2 fix) + APPROVED iter 2 (FE, with WARN documented)
> Final transition: developing → developed → reviewing → done

## § 1 — Gherkin verification matrix

| Scenario (Gherkin) | Test path | Status |
|---|---|---|
| SC-01 — Happy multisession re-engagement (paciente con tratamiento incompleto recibe sugerencia Adrián) | `vitalia/backend/tests/agentic_evals/sales_agent/goldens/reengagement/happy_multi_session.yaml` + `vitalia/frontend/e2e/specs/regression/fidelizacion-multi-session-happy.spec.ts::scenario-01` (compiled scaffold) | ✅ PASS (golden) · 🟡 SCAFFOLD (E2E seed-dependent) |
| SC-02 — Absence without opt-in (paciente sin consent → compliance block) | `vitalia/backend/tests/modules/vitalia/crm/application/test_consent_service.py` + `vitalia/backend/tests/modules/vitalia/fidelizacion/application/test_proactive_outbound_service.py::test_marketing_template_blocked_no_optin` + `vitalia/backend/tests/agentic_evals/sales_agent/goldens/reengagement/absence_optin_guard.yaml` + `fidelizacion-absence-no-optin.spec.ts` (scaffold) | ✅ PASS (BE+golden) · 🟡 SCAFFOLD (E2E) |
| SC-03 — Follow-up doctor vencido (UTILITY template — sin opt-in marketing requerido) | `vitalia/backend/tests/modules/vitalia/fidelizacion/application/test_proactive_outbound_service.py::test_utility_template_passes_without_optin` (★ added in iter 2 F1 fix) + `vitalia/backend/tests/agentic_evals/sales_agent/goldens/reengagement/happy_follow_up.yaml` + `fidelizacion-follow-up-doctor-vencido.spec.ts` (scaffold) | ✅ PASS (BE+golden) · 🟡 SCAFFOLD (E2E) |
| SC-04 — Adversarial (cross-tenant + XSS + RBAC) | `vitalia/backend/tests/integration/test_inbox_send_retract_audit_log.py` (Postgres-gated) + `fidelizacion-adversarial.spec.ts` (scaffold) | 🟡 SCAFFOLD (BE integ auto-skip when Postgres down) |
| a11y axe critical violations (5 tabs) | `vitalia/frontend/e2e/specs/smoke/fidelizacion.smoke.spec.ts::a11y_tab_*` (5 specs) | ✅ PASS 5/5 (live, post iter 1 fix aria-controls scoping) |

## § 2 — Playwright E2E run

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke e2e/specs/smoke/fidelizacion.smoke.spec.ts
```

- Specs run: 15
- Passed: 11 (incluye los 5 a11y axe que estaban fallando pre-iter1)
- Failed: 4 (patient card visibility + 1 Maintenance empty state — todas seed-data / dev DB sin pacientes seed)
- Auditor FE iter 2 APPROVED with WARN explicit per `auditor-self-fix-policy.md` § "Si los fails son SEED DATA / FIXTURE issues (no functional code bugs) → APPROVE con WARN documented".
- Trace artifacts: `vitalia/frontend/test-results/specs-smoke-fidelizacion.s-*/trace.zip`

**Mid-session orchestrator fix (commit eaefd41)**: POM `activeTab()` used `getByRole("navigation")` but FidelizacionTabsBar renders `<nav role="tablist">` — ARIA `role="tablist"` overrides implicit `navigation` from `<nav>` tag. 1-line fix recovered 1 failing test.

## § 3 — Capabilities updated/created

- `vitalia/docs/product/capabilities/crm/crm-consent-optout.yaml` — NEW (consent + opt-out service + audit log + endpoints T-2)
- `vitalia/docs/product/capabilities/sales_agent/adrian-reengagement-tool.yaml` — NEW (send_proactive_reengagement tool T-9, hereda F1 UTILITY/MARKETING fix downstream)
- `vitalia/docs/product/capabilities/agentic/lucas-recommendation-tool.yaml` — NEW (compute_re_engagement_recommendation Lucas T-10 — Opus 4.7 R23)
- `vitalia/docs/product/capabilities/compliance/whatsapp-template-registry.yaml` — NEW (T-8 SSoT registry UTILITY vs MARKETING + requires_marketing_opt_in)
- `vitalia/docs/product/capabilities/patients/nps-tracking.yaml` — NEW (NPS response repository + service + dual filter tenant+clinic + pgcrypto encrypted comment ★ post iter 2 F2)

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/crm.md` — auto-list incluye crm-consent-optout
- `vitalia/docs/product/modules/sales_agent.md` — auto-list incluye adrian-reengagement-tool
- `vitalia/docs/product/modules/agentic.md` — auto-list incluye lucas-recommendation-tool
- `vitalia/docs/product/modules/compliance.md` — auto-list incluye whatsapp-template-registry
- `vitalia/docs/product/modules/patients.md` — auto-list incluye nps-tracking
- (Auto-regen via `scripts/reconcile_capabilities.py --brand vitalia`)

## § 5 — How to verify (reproducible commands)

```bash
# Setup (asumiendo make dev-vitalia corriendo):
WS=$(git rev-parse --show-toplevel)

# 1. BE unit + arch fitness (incluye pgcrypto trigger test + UTILITY/MARKETING)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ tests/modules/vitalia/fidelizacion/ tests/modules/vitalia/crm/ -v
# Expected: 412+ pass, 0 failed (integration auto-skip if Postgres unreachable)

# 2. Migration 025 pgcrypto NPS comment (idempotent IF NOT EXISTS — safe to re-apply)
docker exec luana-dev-vitalia_backend_dev-1 alembic upgrade head
# Expected: 025_vitalia_pgcrypto_nps_comment.py applied · trigger trg_encrypt_nps_comment active

# 3. FE type-check + lint + arch fitness + unit
cd ${WS}/vitalia/frontend && npx tsc --noEmit
cd ${WS}/vitalia/frontend && npx vitest run src/__tests__/architecture/ src/features/fidelizacion/
# Expected: 42 arch + 64 fideliz unit GREEN

# 4. E2E smoke live (stack up: make dev-vitalia, port 3002 FE)
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke e2e/specs/smoke/fidelizacion.smoke.spec.ts
# Expected: 11/15 GREEN (4 remaining are seed-data dependent, Slice 2 BE seed scripts will close gap)

# 5. Agentic eval goldens (smoke)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/agentic_evals/sales_agent/test_voice_fidelity_reengagement.py -v
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/agentic_evals/lucas/ -v
```

**Iter 2 BE fix highlights** (commit 9b676ee):
- F1 RESOLVED: `proactive_outbound_service.py` consults `WHATSAPP_TEMPLATE_REGISTRY.requires_marketing_opt_in` (Slot 5 step 2). UTILITY templates pass without opt-in; MARKETING still gated; unknown → "template_unknown" blocked.
- F2 RESOLVED: Migration `025_vitalia_pgcrypto_nps_comment.py` adds `pgcrypto` BEFORE INSERT/UPDATE trigger encrypting `vitalia_nps_responses.comment` via `pgp_sym_encrypt()` with `app.encryption_key` GUC. Arch test `test_pgcrypto_phi_columns.py` allowlist closed gap. `nps_service.py:125-131` docstring corrected.

**Pre-existing fixture infra fix** (commit 22eaebf): promoted `db_session` async fixture from `tests/integration/conftest.py` to shared `tests/conftest.py` (T-4 integration tests live under `tests/modules/vitalia/fidelizacion/infrastructure/` and needed the fixture available there). 12/12 fideliz integration tests now correctly auto-skip when Postgres unreachable.
