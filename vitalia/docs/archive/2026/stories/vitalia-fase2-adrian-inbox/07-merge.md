---
story_id: vitalia-fase2-adrian-inbox
brand: vitalia
merged_by: /pm-vitalia
merge_date: 2026-06-04
audit_verdict: APPROVED
state: done
cap_change_type: extend
---

# 07-merge — vitalia-fase2-adrian-inbox (2-modos · audit-ready)

> Fase F (story-closure-gate). Auditor APPROVED (8d6d4c40, CHECKPOINTS C1-C5). Modelo 2-modos
> (amendment 2026-06-04, ver `01-spec § Scope amendment`). Demo sign-off Chris APPROVED_WITH_NOTES.

## § 1 — Gherkin verification matrix

Copia de `06-audit/gherkin-matrix.md`: **17/17 reglas PASS · 0 MISSING**.

| Cobertura | Fuente | Status |
|---|---|---|
| RN-1 modo 2-modos · RN-5 pausa · RN-17 composer dock · RN-16 leads visible · RN-6 glass-box · RN-14 deep-link | e2e-live (golden 7 passed) | ✅ |
| RN-2 audit · RN-15 RBAC operador · RN-13 nudge · RN-4 consulta | be-test + e2e-live | ✅ |
| RN-7 PHI firewall · RN-3 escala · RN-10 sanitize · RN-9 tenant isolation · RN-8 RBAC sidebar | be-test | ✅ |
| RN-11 full-canvas · RN-12 reversible (AC-7/AC-12) | shell-story (`vitalia-bugfix-shell-nav-scroll-errors` done) | ✅ |

Detalle + evidencia DB: `06-audit/gherkin-matrix.md`.

## § 2 — Playwright E2E run

```bash
cd vitalia/frontend && set -a; source ../.env.dev; set +a
E2E_BASE_URL=https://dev-app.vitalialat.com \
  npx playwright test e2e/shell-organism/adrian-inbox-modes.spec.ts --project=smoke --no-deps --workers=1
# → 7 passed (golden 2-modos: mode PATCH 200 + pause POST 200 + composer + privacy + glass-box)
```

Verdict: **7 passed** contra dev-app (backend real, 0 mocks, importa `fixtures/base.ts` anti-burbuja). Writes DB-verified (`handler_mode=ai`, `pause_until` set).

## § 3 — Capabilities updated/created

> ★ Reconciliación rigurosa pedida por Chris (2026-06-04): cap canónica completa + mapeo bidireccional code↔cap + regression_tests reales (input del architect) + cero hallucination (todos los paths verificados existentes).

- **CREADA** `vitalia/docs/product/capabilities/inbox/adrian-inbox.yaml` (cap_id `inbox.adrian-inbox`, module=inbox) — **cap canónica del inbox shell-organism**, `status: live`. Matchea los headers reales del código (`# cap: inbox.adrian-inbox` BE · `// cap: adrian.inbox` FE) que antes eran **orphans** (la cap no existía). Contiene:
  - **10 scenarios** (mode/pausa/composer/lead-privacy/glass-box+deeplink/nudge/PHI-firewall/cross-tenant/estados+a11y/full-canvas) — cada uno wired a un e2e_test REAL (cross_check_3 HARD = **106/106, 0 drift**).
  - **`code_pointers`** (bidireccional): BE api/services/policies/persistence/session-lifecycle + FE main_component/components/hooks/route. El architect lo usa para saber qué tocar + qué regresión correr.
  - **`regression_tests`** (★ input del architect): cada comportamiento → su batería de tests REAL (BE 103 + FE 344 + 6 e2e specs + db-persistence-proof). Verificado existente.
  - **`business_rules`** con `code_ref` exacto, incl. `inbox-mutation-commits` (HB-50: mutación → `get_async_session_committing` + test de persistencia).
  - access api entry_points → enforcement `_assert_phi_access(_INBOX_OPERATOR_ROLES)` resuelto vía router.py (cross_check_4 PASS para esta cap).
- **DEPRECATED/SUPERSEDED** `vitalia/docs/product/capabilities/sales_agent/inbox-handler-mode-occ.yaml` — slice-1 legacy. `superseded_by: inbox.adrian-inbox`; api entry_points movidos a la cap canónica (drift cross_check_4 eliminado). Conserva registro histórico.
- `copilot/inbox-tools-extensions.yaml` — sin cambios (tool registry, concern separado).
- Bidireccional: cross_check_3 HARD **106/106 (0 drift)**; cross_check_4 1 drift PRE-EXISTENTE (`compliance.hipaa-lite-defensive-stack`, módulo distinto, no-inbox — fuera de scope).

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/inbox.md` (o `sales_agent.md`) auto-list refresh (post `make portfolio`).

## § 5 — How to verify (reproducible)

```bash
WS=$(git rev-parse --show-toplevel)
# BE regression (commit-fix HB-50)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/inbox/ -q          # 103 passed
${WS}/.venv/bin/ruff check src/modules/vitalia/inbox/                                          # clean
# FE
cd ${WS}/vitalia/frontend && npx tsc --noEmit                                                  # 0
npx eslint src/features/adrian/ --cache                                                        # 0
npx vitest run src/features/adrian/                                                            # 344 passed
# Golden live (dev-app)
set -a; source ../.env.dev; set +a; E2E_BASE_URL=https://dev-app.vitalialat.com \
  npx playwright test e2e/shell-organism/adrian-inbox-modes.spec.ts --project=smoke --no-deps --workers=1   # 7 passed
# DB persistence proof
docker exec luana-dev-luana_postgres_dev-1 psql -U postgres -d vitalia_dev \
  -c "SELECT id, handler_mode, pause_until IS NOT NULL AS paused FROM vitalia_conversations WHERE id IN ('11111111-1111-5111-8111-111111111111','22222222-2222-5222-8222-222222222222');"
```

## § Verificación live (DoD #37)

`dod_live_verified: true` + `dev_app_verified` (ADR-vitalia-008) en `checkpoint.md`. Writes reales ejercidos + efecto en DB confirmado. demo_signoff Chris APPROVED_WITH_NOTES (open_items severity low, diferidos).

## § Hallazgo cementado (HB-50)

El golden cazó un bug sistémico que el optimistic-UI + el check-solo-200 ocultaban: las 6 mutaciones del inbox (mode/pause/send/proactive/nudge/retract) devolvían 200 pero **nunca commiteaban** (`get_async_session` no commitea + ningún service commitea). Fix: factories → `get_async_session_committing`. 3ra instancia de verificación-≠-200 → `docs/process/harness-backlog.md` HB-50 (promotable cross-brand).

## § Follow-ups (no bloquean done — `06-tickets.yaml § follow_ups`)

FU-1 Máxima seguridad config · FU-2 nudge/retract/proactive query-keys · FU-3 pausa permanente real · FU-4 consolidar _INBOX_OPERATOR_ROLES · FU-5 detalles estéticos · FU-6 use-set-mode optimistic updated_at · FU-7 live-verify retract.
