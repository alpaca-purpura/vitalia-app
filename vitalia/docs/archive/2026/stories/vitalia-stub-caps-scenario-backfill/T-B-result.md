---
ticket: T-B
story_id: vitalia-stub-caps-scenario-backfill
brand: vitalia
group: G2
surface: docs
production_code: false
completed_at: 2026-05-30
builder: claude-sonnet-4-6
---

# T-B Result — G2 Admin panel (5 caps)

## Skills consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `frontend-expert` | Obligatorio siempre — runtime checklist + FSD | Confirmado: esta tarea es docs-only, no production code. No requiere "use client", hooks, ni componentes. |
| `brand-expert` | Obligatorio siempre — field-contract-platform | Confirmado: no se toca brand studio / field_contract; los cap YAMLs son docs de producto, no del módulo brand. |
| `offer-expert` | Declarado por rol — offer studio | Confirmado: no aplica (caps admin, no offer studio). |
| `offer-type-preset-expert` | Declarado por rol | No aplica. |
| `copilot-expert` | Declarado por rol | No aplica. |
| `sales-agent-expert` | Declarado por rol | No aplica. |
| `metrics-expert` | Declarado por rol | No aplica. |
| `chrome-devtools-verify` | Live verification gate | Admin Streamlit NO está levantado en este entorno (ver §Entorno). Documentado como PENDING_DEPLOY per protocolo de la story. |
| `.claude/rules/test-design-doctrine.md` | Bar deployed-visible | Verificación REAL ≠ HTTP 200: los admin specs requieren Streamlit levantado. Sin éste → caps quedan como partial por entorno (ver §Entorno). |

## Resumen ejecutivo

Se appendaron bloques `scenarios:` y entradas `change_log` a los 5 caps G2 del módulo admin, cableando cada scenario a su spec Playwright existente. El gate HARD `cross_check_3 drift=0` se mantiene limpio (exit 0).

Los admin specs corren contra Streamlit (:8501/:8502), que **no está levantado en este entorno local**. Per protocolo de la story (01-spec.md § "⚠️ Los admin specs corren contra Streamlit"): si el admin Streamlit NO está levantado → documentar como `PENDING_DEPLOY` y no forzar verde. La computed_status que arroja `compute_capability_status.py` es `verified-live` porque el gate chequea **existencia del archivo + patrón `test(`**, no que el test corra. La verificación real desplegada (bar deployed-visible) queda pendiente para el orchestrador en dev-app.

## Por-cap tabla de resultados

| cap | spec cableado | spec existe | spec corrió | computed_status | relevancia del test | resultado |
|---|---|---|---|---|---|---|
| `admin-streamlit-service` | `e2e/admin/admin-login.spec.ts` | ✅ | ❌ PENDING_DEPLOY (Streamlit down) | verified-live (gate mecánico) | ✅ el spec ejercita login admin + sidebar navegación | partial-pending-deploy |
| `clinics-crud` | `e2e/admin/admin-clinics-extension.spec.ts` | ✅ | ❌ PENDING_DEPLOY (Streamlit down) | verified-live (gate mecánico) | ✅ el spec crea clínica + audit log + listado columnas | partial-pending-deploy |
| `tenants-crud` | `e2e/admin/admin-tenants-crud.spec.ts` | ✅ | ❌ PENDING_DEPLOY (Streamlit down) | verified-live (gate mecánico) | ✅ el spec crea/lista/suspende tenants + audit log | partial-pending-deploy |
| `users-crud` | `e2e/admin/admin-users-crud.spec.ts` | ✅ | ❌ PENDING_DEPLOY (Streamlit down) | verified-live (gate mecánico) | ✅ el spec crea/lista/banea usuarios + audit log | partial-pending-deploy |
| `streamlit-tenants-users` | `e2e/admin/tenants-users.spec.ts` | ✅ | ❌ PENDING_DEPLOY (Streamlit down) | verified-live (gate mecánico) | ✅ el spec verifica navegación Tenants+Usuarios + no-PHI | partial-pending-deploy |

## Entorno — por qué PENDING_DEPLOY

```
curl http://localhost:8502/_stcore/health → 000 UNAVAILABLE
curl http://localhost:8501/_stcore/health → 000 UNAVAILABLE
```

El admin Streamlit requiere `make dev-vitalia-admin` (Docker) que no está levantado en esta sesión de build. Per 01-spec.md §G2 nota: "los admin specs corren contra Streamlit (:8502). El builder confirma que corren verde en el entorno e2e; si están skip/quarantine → escala (no se cablea un test que no corre)." Los specs NO están skip/quarantine — la razón de no-correr es infraestructura (Docker down), no defecto del spec. El orchestrador debe ejercerlos contra dev-app (admin.vitalialat.com) o local con `make dev-vitalia-admin`.

## Gate output

```
compute_capability_status.py --brand vitalia (post-backfill):
  68 caps · stub=16 · declared-live=0 · verified-live=13 · drift=0 · partial=6 · wip=0 · deprecated=33
  5 caps G2: todos computed → verified-live ✅ (gate mecánico: archivo existe + test( patrón)

validate_code_cap_bidirectional.py --brand vitalia --strict:
  cross_check_3: total=80 pass=80 drift=0 ✅ (HARD gate limpio)
  cross_check_4: total=12 pass=11 drift=1 (pre-existente — roles decorators gap, no introducido por T-B)
  Verdict: SOFT_DRIFT · exit=0 ✅
```

## Scenarios appendados por cap

### admin-streamlit-service (2 scenarios)
- `admin-login-bcrypt-dashboard-accesible` — SC-01 del spec: login correcto → sidebar con Tenants + Usuarios
- `admin-sin-sesion-muestra-login` — SC-12 del spec: sin sesión → formulario password visible

### clinics-crud (2 scenarios)
- `admin-crea-clinica-asociada-tenant` — SC-08 del spec: crea clínica + audit log action=clinic.create
- `admin-listado-clinicas-columnas-visibles` — SC-13 del spec: listado muestra Nombre/Slug sin errores DB

### tenants-crud (3 scenarios)
- `admin-crea-tenant-nuevo-audit-log` — SC-02: crea tenant + audit log action=tenant.create
- `admin-lista-tenants-columnas-sin-phi` — SC-03: listado Nombre/Slug + no-PHI
- `admin-suspende-tenant-audit-log` — SC-07: toggle is_active + audit log tenant.suspend/activate

### users-crud (3 scenarios)
- `admin-crea-usuario-asigna-tenant` — SC-04: crea user + audit log action=user.create
- `admin-lista-usuarios-columnas-sin-phi` — SC-05: listado Email/Nombre + no-PHI
- `admin-banea-usuario-audit-log` — SC-06: toggle is_active + audit log user.ban/activate

### streamlit-tenants-users (2 scenarios)
- `admin-panel-tenants-navegacion-formulario` — SC-08 del spec: navegación + formulario crear tenant
- `admin-panel-usuarios-formulario-sin-phi` — SC-09 del spec: formulario crear usuario + no-PHI

## Verificación de relevancia (anti-teatro SC-4)

Los specs cableados **genuinamente ejercitan** el comportamiento declarado en los scenarios:
- `admin-login.spec.ts` → ejercita login bcrypt + sidebar navigation (SC-01 + SC-12)
- `admin-clinics-extension.spec.ts` → navega a Clínicas, crea clínica, verifica DB count + audit log (SC-08), verifica columnas listado (SC-13)
- `admin-tenants-crud.spec.ts` → crea tenant + verifica DB count + audit log (SC-02), verifica columnas (SC-03), toggle suspender + audit log (SC-07)
- `admin-users-crud.spec.ts` → crea user + verifica DB count + audit log (SC-04), verifica columnas (SC-05), toggle banear + audit log (SC-06)
- `tenants-users.spec.ts` → verifica navegación Tenants+Usuarios + formularios (SC-08/SC-09), verifica no-PHI

Los tests ejercitan el comportamiento descrito — no son proxies desconectados.

## Próximo paso (orchestrador)

Levantar `make dev-vitalia-admin` y correr:
```bash
cd vitalia/frontend && E2E_ADMIN_BASE_URL=http://127.0.0.1:8502 \
  VITALIA_ADMIN_PASSWORD="${VITALIA_ADMIN_PASSWORD}" \
  npx playwright test e2e/admin/ --project=admin-smoke
```

Si verde → actualizar esta tabla reemplazando `partial-pending-deploy` con `verified-live (deployed-visible)` en VERIFICATION-REPORT.md.
