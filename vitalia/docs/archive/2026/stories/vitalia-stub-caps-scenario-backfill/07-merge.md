---
story_id: vitalia-stub-caps-scenario-backfill
brand: vitalia
merged_at: 2026-05-30
state: done
auditor_verdict: APPROVED
cap_change_type: extend
---

# 07-merge — Backfill scenarios+e2e para 20 caps stub

> Auditor APPROVED (independiente, auditor-backend Opus) → `T-audit-review.md`. Merge en wip/vitalia (hub). Integración a `main` = paso manual de Chris (staging deploy manual, git-safety).

## § 1 — Verificación matrix (resultado honesto · deployed-visible bar)

**14 verified-live + 6 partial** (de 20). El cockpit refleja la realidad (no la existencia-de-archivo). cross_check_3 **drift=0, exit 0** (HARD limpio). Detalle por-cap: `VERIFICATION-REPORT.md`.

| Grupo | verified-live | partial (honesto) |
|---|---|---|
| G1 UI-visible | design-tokens-theme, design-tokens-foundation, topbar-global, shell-foundation-shadcn-tailwind-v4, sign-in-sign-up-pages | iam-scaffold-slice-1, public-clinic-landing |
| G2 admin | admin-streamlit-service | tenants-crud, users-crud, clinics-crud, streamlit-tenants-users |
| G3 infra | api-health-endpoint, playwright-smoke-suite | — |
| G4 backend | hipaa-dual-filter-decorator, audit-writer-ssot, migrations-slice-1-schema, idempotent-cron-arq-scaffold, otel-sentry-graceful-degradation, vitalia-callback-subclasses | — |

Los 6 partial NO fueron forzados a verified-live falso (anti-teatro): cada uno tiene ≥1 scenario `e2e_test: null` + rationale. Razones: iam-scaffold (nav e2e POM bug ribbon-testid), public-clinic-landing (2 scenarios → fixture Fase 2 `3-clinic-fixture-latam`), 4 admin CRUD (panel verificado hands-on + db-state fixed, pero writes UI no ejercidos por selectores Streamlit frágiles).

## § 2 — Tests / gates run (evidencia)

```
python3 scripts/compute_capability_status.py --brand vitalia
  → 68 caps · verified-live=16 (target 14 + 2 previos) · partial=11 · drift=0
python3 scripts/validate_code_cap_bidirectional.py --brand vitalia --strict
  → cross_check_3 total=90 pass=90 drift=0 · exit 0 (HARD) · cross_check_4 drift=1 (RBAC advisory pre-existente)
.venv/bin/pytest scripts/tests/test_validate_code_cap_bidirectional.py -q → 19 passed
cd vitalia/backend && pytest (G4 wired) → 69 passed, 8 skipped (otel graceful by design)
curl https://dev-app.vitalialat.com/api/health → 200 {"status":"ok","brand":"vitalia"}
curl https://dev-app.vitalialat.com/sign-in → 200 + markers clerk/sign-in
admin-login.spec.ts vs Streamlit :8502 → 3/3 PASS
```

## § 3 — Capabilities updated (Fase F.3 · cap_change_type: extend)

20 cap YAMLs recibieron `scenarios[]` append + `change_log` entry (type: extend, added_in_story: vitalia-stub-caps-scenario-backfill). Paths: `vitalia/docs/product/capabilities/{platform,auth,iam,public_landing,admin,observability,clinics,audit,workers,tests}/{cap}.yaml`. NO se crearon caps nuevos (extend coherente). NO se tocó `status` (sigue `live`); cambió el `computed_status` derivado.

## § 4 — Fix-to-green incluido (excepción ratificada)

1 bug real encontrado + arreglado (commit `882f9f49`): endpoints helper del admin (`/db-state`, `/audit-log`, `/tenants-exists`, `/clinics-exists`, `/audit-log/count`) usaban `async for db in get_db()` con el `get_db` **sync** del engine → 500 `'async for' requires __aiter__`. Fix: `get_async_session` (`src.db`), mismo patrón que payments/scheduling. Auditor APPROVED. db-state ahora 200. Desbloqueó la verificación e2e del admin (caps G2).

## § 5 — How to verify (reproducible)

```bash
WS=$(git rev-parse --show-toplevel); cd ${WS}
python3 scripts/compute_capability_status.py --brand vitalia            # 14 target verified-live + 6 partial
python3 scripts/validate_code_cap_bidirectional.py --brand vitalia --strict   # exit 0, cross_check_3 drift=0
.venv/bin/pytest scripts/tests/test_validate_code_cap_bidirectional.py -q     # 19 passed (T-0)
# Cockpit /drift: estos 20 dejan de aparecer como drift (status honesto)
```

## Deuda follow-up (3 stories candidatas · NO esta story)

1. **admin-e2e-selector-hardening** — robustecer 9 admin specs frágiles (`st.dataframe` canvas headers + `getByLabel` que matchea botón Help). Llevaría los 4 admin CRUD partial → verified-live.
2. **clerk-testing-token-e2e** — CLERK_TESTING_TOKEN en sign-in-form.spec.ts (widget interaction). Refuerza sign-in.
3. **iam-nav-pom-fix** — fix POM ribbon-testid strict-mode en happy-navigation.spec.ts. Llevaría iam-scaffold partial → verified-live.

## Slice 2 PHI (desacoplado — story propia, NO esta)

MEDIDO: ningún cap de los 20 requiere el decoder PHI. Slice 2 (desentubar JWKS real + rol desde user_tenants + repos reales) = deuda arquitectónica real, story siguiente en esta sesión.
