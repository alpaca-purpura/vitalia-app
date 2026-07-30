# 07-merge — vitalia-fase2-config-cuenta

> /pm-vitalia · Fase F MERGE · 2026-06-12 · autonomous_mode (D-AUTO Chris: full unattended, demo_required override→false)
> Auditor verdict: APPROVED (CHECKPOINTS.md C1-C5 ✅ · T-1 APPROVED · T-2 APPROVED iter 2)

## § 1 — Gherkin verification matrix

Copia consolidada: `06-audit/gherkin-matrix.md` — **12/12 PASS · 0 MISSING · 0 FAIL**.
Happy path completo `✅ construido` (cap_change_type=new → piso HARD cumplido).
Bar: acción REAL ejercida + efecto observado (writes live, audit row en DB, negativos 422/403/404).

## § 2 — Playwright E2E run

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test config-cuenta.spec --project=smoke
```
**Verdict: 6/6 PASSED** (Clerk auth real dr.demo + BE real :8002 via real-backend-forward.fixture
(composición base.ts anti-burbuja) · NO mocks del surface · incluye SC-04 WRITE real:
edit → autosave → PATCH 200 → reload persiste → restore).

Verificación adicional del auditor (independiente): PATCH live → `vitalia_audit_log` count 1→2 ·
specialty inválida → 422 → count NO incrementa + atomicidad negativa confirmada.

## § 3 — Capabilities updated/created

- `vitalia/docs/product/capabilities/configuracion/cuenta.yaml` — **planned → live** (cap_change_type=new):
  12 scenarios v3.2 (`verified_real: true` ×12) · access (write: owner/admin_clinic) ·
  business_rules RN-1..RN-6 con enforcement+code_ref · dev_preview completo (ruta/component/endpoints/e2e) ·
  change_log[0] type=new.
- `vitalia/docs/architecture/SYSTEM-MAP.yaml` — `configuracion.cuenta` status planned→**live** (F4, sin billing D1).
- `make cap-doctor BRAND=vitalia` → ✅ SANO (75 caps, 0 deriva).

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/configuracion.md` — auto-list regenerado via `make portfolio` (cuenta → live).

## § 5 — How to verify (reproducible)

```bash
# Stack
make dev-vitalia   # BE :8002 + FE :3002 (migración 039 aplicada)

# BE suite + integration audit-durability (real DB)
cd vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/clinics/ -q

# FE gates
cd vitalia/frontend && npx tsc --noEmit && npx vitest run src/features/config/

# E2E browser real
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test config-cuenta.spec --project=smoke

# Live manual: login dr.demo@vitalialat.com → Plataforma → Mi cuenta → editar nombre/CUIT/especialidad
# → autosave → recargar (persiste) → audit row:
docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && /workspace/.venv/bin/python -c \"
import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
async def m():
    e = create_async_engine(os.environ['DATABASE_URL'])
    async with e.connect() as c:
        print((await c.execute(text(\\\"SELECT COUNT(*) FROM vitalia_audit_log WHERE action='clinic_account_patch'\\\"))).scalar())
asyncio.run(m())\""
```

## Commits de la story

| SHA | Qué |
|---|---|
| `ce34c4b0` | T-2 BE (campos + validators + router + migración 039) |
| `5cc668d8` | T-1 FE (N3-static + autosave + specialties + contract-parity HARD) |
| `120f5390` | fixes back-compat language=None + de-flake doctor tests |
| `0350bd73` | fix-session live-verify: 7 bugs integración + ui-kit N3 lift regression hotfix |
| `5b629365` | C9-1 audit-row durability (atomic unit-of-work) + audit APPROVED artifacts |
| (este) | Fase F: cap live + SYSTEM-MAP + 07-merge + learning + archive R2 |

## Escalables registrados (→ /pm-luana)

1. **F-engine-me-role-drift** (MED): engine iam `GET /me` devuelve `users.role` legacy global ≠ `user_tenants.role` per-tenant. Workaround brand: `useTenants()`. Proposal pendiente.
2. **ui-kit hotfix retroactivo**: `subSubTabsByKey` wire + `configTabSlug` en validSlugs (regresión del lift 3cb9d5a0 — barra N3 muerta plataforma-wide). Cambio additive backward-compat ya aplicado; proposal retroactiva pendiente.
3. **Lift candidates** (NO lift 1ª impl): `fiscal_id_validator` + `specialty_catalog` (multi-país).

## Deuda ruteada
- `test_pgcrypto` treatment_plans.notes TEXT (migración 005, módulo treatment — pre-existente) → backlog vitalia.
- Visual goldens PNG (cuenta-{datos,prefs,resp}) — WARN no-bloqueante; generar en follow-up.
- F-RBAC-consistency: migrar check del service al `Depends(require_brand_owner_access)` — next-story candidate.
