---
proposal_id: 2026-06-04-nicolify-abel-w1-auth-w2-growth-emitter
state: proposed
opened_date: 2026-06-04
opened_by: /dev-team (nicolify-r1-abel-icp-buyer)
ratified_by: pending           # Chris eligió "graduar follow-up vía /pm-luana" (2026-06-04)
ratified_date: null
migrated_date: null

# Origen
origin_story: nicolify/docs/product/stories/nicolify-r1-abel-icp-buyer
origin_audit: 06-audit · W1 (security WARN) + W2 (anti-dup lift candidate N=2)
origin_brands: [nicolify]

# Target
target_package: W1 → nicolify brand-local (consume core/luana-core-iam verify_clerk_token) · W2 → core/luana-core-observability o core/luana-core-events
target_ep: null
breaking_change: false
semver_bump: minor
brands_affected_consumers: [nicolify, vitalia, comunify, lupulo]
---

# Proposal — W1 (app-layer auth en rutas abel) + W2 (lift GrowthStudioEmitter)

Dos follow-ups graduados del cierre de `nicolify-r1-abel-icp-buyer`. Ambos NO-bloqueantes
para el `done` de esa story (el audit los marcó WARN; el aislamiento por query HOLDS en
dev/localhost). Chris ratificó "graduar follow-up vía /pm-luana" (2026-06-04).

## W1 — Auth Bearer app-layer en las rutas `abel`

**Hallazgo (audit):** las rutas `nicolify/backend/src/modules/nicolify/abel/api/router.py`
confían en el header `X-Tenant-ID` SIN verificar un Bearer/JWT a nivel app. El aislamiento
por query (`.where(tenant_id == ...)`) HOLDS (sin leak cross-tenant — verificado live: GET
con tenant ajeno → 404). Pero un cliente non-localhost podría mandar cualquier `X-Tenant-ID`.
En dev/demo NO es explotable (Clerk protege en el edge del FE + el proxy Next).

**Es BRAND-LOCAL, no core:** el engine YA expone la dependencia
`core/luana-core-iam/src/luana_core_iam/application/auth.py::verify_clerk_token`
(HTTPBearer + JWKS). NO requiere editar core.

**Diseño del fix (story propia):**
1. BE: agregar `Depends(verify_clerk_token)` a las rutas abel; **cross-check** que el
   `tenant_id` de los claims del JWT == el `X-Tenant-ID` del header (rechazar mismatch → 403).
2. FE: `fetchClient` debe adjuntar el `Authorization: Bearer <clerk session token>` (hoy
   adjunta `X-Tenant-ID`; falta el Bearer). Verificar que `getToken()` esté disponible en
   todos los call sites abel.
3. Tests: 401 sin Bearer · 403 si el claim tenant ≠ header · 200 con ambos coherentes.

**Por qué follow-up, no en la story:** toca FE (fetchClient) + BE (cross-check) en TODAS las
rutas abel → scope real que merece su propia security-story con su batería de tests. El audit
lo ratificó no-bloqueante para localhost/dev. Generalizable: la MISMA brecha aplica a otras
rutas brand que hoy confían solo en `X-Tenant-ID` → candidato a un patrón cross-brand
(`require_tenant_match` dep en core que combine verify_clerk_token + el cross-check).

## W2 — Lift `GrowthStudioEmitter` (anti-dup N=2)

**Hallazgo (audit Cat 12):** `GrowthStudioEmitter` (telemetría brand-local de nicolify, tabla
`nicolify_growth_studio_event`) es un patrón legítimo brand-local, PERO es **lift candidate
N=2** — si otra brand replica el mismo emitter de eventos de producto, hay que liftarlo a core
antes del mirror (`.claude/rules/anti-duplication.md`).

**Diseño del lift (cuando N=2 se materialice):**
- Lift la lógica de emisión (`emit(event_name, props, no-PII via hash)` + best-effort + outbox)
  a `core/luana-core-observability` o `core/luana-core-events` como base class /
  `BaseProductEventEmitter`, con la tabla per-brand (`{brand}_growth_studio_event`) inyectada.
- Nicolify (+ futuras) heredan vía Extension SDK; cero mirror.

**Por qué follow-up:** hoy N=1 (solo nicolify). El lift es prematuro hasta que una 2da brand
necesite el mismo emitter. `/pm-luana` lo agenda cuando aparezca el 2do consumer.

## Acceptance criteria

- [ ] `/pm-luana` agenda W1 como security-story (nicolify, brand-local) + evalúa el patrón
      cross-brand `require_tenant_match`.
- [ ] `/pm-luana` marca W2 como "esperar N=2" (no liftar prematuro) o liftar si ya hay 2do consumer.
- [ ] Ninguno bloquea el `done` de `nicolify-r1-abel-icp-buyer`.
