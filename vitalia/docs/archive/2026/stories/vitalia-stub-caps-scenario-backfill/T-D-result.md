---
ticket: T-D
story_id: vitalia-stub-caps-scenario-backfill
brand: vitalia
surface: docs
production_code: false
completed_at: 2026-05-30
builder: claude-sonnet-4-6
commit: 899803e4
---

# T-D Result — Consolidacion honesta + VERIFICATION-REPORT

## Skills Consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `backend-expert` | Obligatorio — runtime checklist, antipatrones FastAPI/SQLA | Confirmado: T-D es docs-only, no production code. No requiere capas DDD, migraciones, ni tests. |
| `brand-expert` | Verificar scope brand | No aplica (no se toca field_contract ni módulo brand). |
| `offer-expert` | Verificar scope offer studio | No aplica (caps admin/iam/tests, no offer). |
| `offer-type-preset-expert` | Verificar scope presets | No aplica. |
| `metrics-expert` | Verificar scope analytics | No aplica. |

## Resumen

T-D completado. Consolidación honesta con antitheatro aplicado:

1. **TAREA 1 — 5 caps bajados a partial** (scenario con `e2e_test: null` appendado):
   - `iam/iam-scaffold-slice-1.yaml` → scenario `iam-routing-nav-e2e-pendiente-hardening`
   - `admin/tenants-crud.yaml` → scenario `tenant-write-ui-e2e-pendiente-hardening`
   - `admin/users-crud.yaml` → scenario `user-write-ui-e2e-pendiente-hardening`
   - `admin/clinics-crud.yaml` → scenario `clinic-write-ui-e2e-pendiente-hardening`
   - `admin/streamlit-tenants-users.yaml` → scenario `tenant-user-link-write-ui-e2e-pendiente-hardening`

2. **TAREA 2 — playwright-smoke-suite re-apuntado**:
   - Antes: `sign-in-form.spec.ts` (2/4 falla, Clerk JS no carga en test env)
   - Ahora: `topbar-interaction.smoke.spec.ts` (6/7 pasan, smoke representativo verde, 1 flaky timing no es cap break)
   - Corrida confirmada: `6 passed (8.3s), 1 flaky (retry #1 succeeded)`

3. **TAREA 3 — VERIFICATION-REPORT.md** escrito con tabla completa 20 caps, evidencia real (no teatro), bug db-state documentado, deuda follow-up.

## Gate outputs

### compute_capability_status.py (post-T-D)

```
Procesando 68 capabilities de vitalia..........
Completado: 68 caps · stub=8 · declared-live=0 · verified-live=16 · drift=0 · partial=11 · wip=0 · deprecated=33
```

Bajaron 5 caps de verified-live a partial (16 vs 21 previo). Partial sube de 6 a 11.

### validate_code_cap_bidirectional.py --strict

```
Loaded 68 caps from vitalia
Running cross-check 3 (scenarios e2e_test paths)...
  total=90 pass=90 drift=0
Running cross-check 4 (access roles ↔ decorators)...
  total=12 pass=11 drift=1

Verdict: SOFT_DRIFT
Drift total: 1 · in HARD checks ([3]): 0
exit=0
```

cross_check_3 drift=0: todos los e2e_test no-null existen. Los e2e_test:null (scenarios parciales) no cuentan para cross_check_3 por diseño del validador.
cross_check_4 drift=1: pre-existente (gap RBAC decorators — no introducido por T-D).

## Archivos tocados (7)

1. `vitalia/docs/product/capabilities/iam/iam-scaffold-slice-1.yaml` — +1 scenario partial
2. `vitalia/docs/product/capabilities/admin/tenants-crud.yaml` — +1 scenario partial
3. `vitalia/docs/product/capabilities/admin/users-crud.yaml` — +1 scenario partial
4. `vitalia/docs/product/capabilities/admin/clinics-crud.yaml` — +1 scenario partial
5. `vitalia/docs/product/capabilities/admin/streamlit-tenants-users.yaml` — +1 scenario partial
6. `vitalia/docs/product/capabilities/tests/playwright-smoke-suite.yaml` — re-point e2e_test a topbar-interaction.smoke.spec.ts
7. `vitalia/docs/product/stories/vitalia-stub-caps-scenario-backfill/VERIFICATION-REPORT.md` — creado

## Próximo paso

Story `vitalia-stub-caps-scenario-backfill` en estado `developed`. Listo para handoff a `/auditor`.

Deuda follow-up documentada en VERIFICATION-REPORT.md:
- `admin-e2e-selector-hardening` (selectores Streamlit frágiles)
- `clerk-testing-token-e2e` (sign-in widget test)
- `iam-nav-pom-fix` (ribbon testid duplicado)
