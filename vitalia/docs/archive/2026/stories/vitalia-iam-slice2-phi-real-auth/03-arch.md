---
story_id: vitalia-iam-slice2-phi-real-auth
brand: vitalia
arch_version: 1
schema_version: v4.1
architecture_pattern: ADR-vitalia-004
adr_004_compliance: n/a-with-rationale   # BE-auth wiring + 1 FE hook; NO sub-tab UI nueva (rationale § Architecture Decisions)
architect_run_on: 2026-05-30
cap_target: iam-scaffold-slice-1
cap_change_type: extend
autonomous_mode: false                    # HARD false — auth/PHI (architect-autonomous-mode.md)
---

# 03-arch — Slice 2 PHI: decoder JWT real (JWKS) + rol desde DB + repos reales

## 0. Context Summary

- **Story:** vitalia-iam-slice2-phi-real-auth · `state: refined → ready`
- **Architect run on:** 2026-05-30 (Opus 4.8 cutoff Jan 2026; sin research externo — todo se resuelve consumiendo engine ya presente in-repo, ver § Research Notes)
- **Modulos tocados:** `iam` (auth core) · `crm` (+ consent) · `marketing` · `inbox` (wiring DI repos reales) · FE 1 hook de rol
- **Origen:** hallazgo de `vitalia-stub-caps-scenario-backfill` (done) — el decoder Slice-1 stub rechaza el JWT real de Clerk → ningun cap PHI verificable live.

### Surface -> builder -> auditor mapping (para /dev-team spawn)

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/iam/**` (decoder JWKS + role-from-DB resolver) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| `vitalia/backend/src/modules/vitalia/{crm,marketing,inbox}/api/**` (wiring DI repos reales) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| `vitalia/backend/tests/{integration,architecture}/**` | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| `vitalia/frontend/src/hooks/useCurrentUser.ts` (rol desde `/me`) | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |

> NO agentic. NO Opus-required (no toca `copilot`/`sales_agent`). Todos los tickets `model_preference: sonnet`.

### Skills consultados (decision tomada, no body)

- `backend-expert`: Inside-Out DDD; el resolver de rol vive en `iam/application/services/` (orquestacion), el decoder en `iam/infrastructure/`. SQLA 2.0 async para la query de rol.
- `frontend-expert`: cambio FE minimo — `useCurrentUser` consume `GET /api/v1/iam/users/me` via React Query; NO toca `components/ui/` ni layout.
- `hipaa-lite` (overlay): dual filter tenant+clinic + audit sync + sanitization + `@require_phi_access` ya existen; esta story NO los reescribe, solo cablea repos reales para que corran de verdad.
- `tessl__fastapi` / `tessl__pytest-api-testing`: patron `Depends` para inyectar repos reales + `verify_token_payload` reuse.

### CONTEXT-BRIEF source

No hubo `CONTEXT-BRIEF.md` (story chica BE-auth). **Path B (self-ran greps)** ejecutado — ver § Existing systems audit.

### capability YAML afectado (post-merge)

- `vitalia/docs/product/capabilities/iam/iam-scaffold-slice-1.yaml` — `cap_change_type: extend`, append `change_log` entry + scenarios SC-1..SC-4 al array `scenarios[]` con `added_in_story: vitalia-iam-slice2-phi-real-auth`. NO crea cap nuevo.

### Architecture gates que deben seguir verdes

- `vitalia/backend/tests/architecture/test_phi_dual_filter.py`
- `vitalia/backend/tests/architecture/test_audit_log_sync_write.py`
- `vitalia/backend/tests/architecture/test_audit_log_row_per_phi_endpoint.py`
- `vitalia/backend/tests/architecture/test_response_model_required.py`
- `vitalia/backend/tests/architecture/test_no_phi_in_url_params.py`
- **NUEVO:** `vitalia/backend/tests/architecture/test_auth_stub_env_gate.py` (Q2 — runtime nunca setea `VITALIA_AUTH_STUB`)

---

## Existing systems audit (NO NEW LAYER rule)

### Source of evidence
- [ ] CONTEXT-BRIEF.md § 7 + § 8 — ausente (no se genero)
- [x] Self-run greps (Path B)
- [ ] Re-validacion scan-incomplete

### Audit cross-module ejecutado

```bash
WS=/home/chalreme/Proyectos/luana-vitalia
grep -rln "PyJWKClient|verify_token_payload|JWKS_URL" core/luana-core-*/src vitalia/backend/src
#  -> SOLO core/luana-core-iam/src/luana_core_iam/{application/auth.py, api/dependencies.py}
for b in nicolify comunify lupulo; do find $b/backend/src -name "clerk_jwt_decoder.py" -o -name "clinic_resolver.py"; done
#  -> vacio (cero mirror cross-brand)
grep -rln "VITALIA_AUTH_STUB" vitalia/  ->  solo story docs (NUNCA runtime config)
```

### Sistemas existentes encontrados

| Sistema | Path | Enum/Config | Factory/Router | Providers/Adapters | Estado |
|---|---|---|---|---|---|
| JWKS Clerk verifier | `core/luana-core-iam/.../application/auth.py::verify_token_payload` | `CLERK_ISSUER` env + `PyJWKClient(JWKS_URL)` | — | RS256, leeway 60s, `verify_aud:False` | active |
| Role-from-DB resolver (engine) | `core/luana-core-iam/.../api/dependencies.py::get_current_user` | — | FastAPI Depends | resuelve `user.role = user_tenant.role` por `(user_id, tenant_id, X-Tenant-ID)` | active (sync `Session`) |
| `user_tenants` model + repo | `core/luana-core-iam/.../models/user_tenant_model.py` + `repositories/user_tenant_repository.py` | `role` column | — | sync `Session`, key `(user_id UUID, tenant_id UUID)` | active |
| Engine `/me` router | `core/luana-core-iam/.../api/routers/auth_router.py` (mounted `/api/v1/iam/users`) | — | `get_user_from_token` | devuelve `User{role,...}` | active (montado en `main.py`) |
| Brand stub decoder | `vitalia/.../iam/infrastructure/clerk_jwt_decoder.py` | `_STUB_PREFIX="stub:"` | `ClerkJwtDecoder.decode` | parsea `stub:...`, rechaza JWT real -> JwtDecodeError | **a reemplazar** |
| Brand `ClinicResolver`/`ClinicContext` | `vitalia/.../iam/application/services/clinic_resolver.py` | — | construido inline por routers | hoy saca rol del **token** | **a modificar** (rol desde DB) |
| `@require_phi_access` + `AuditLogRepository` (async) | `vitalia/.../_shared/auth/rbac.py` + `_shared/repositories/audit_log_repository.py` | `PHI_ALLOWED_ROLES` | decorator + Depends | sync-awaited audit write | active — **reusar tal cual** |
| `PhiRepositoryBase` + repos PHI reales | `vitalia/.../_shared/repositories/phi_repository.py` + `crm/.../patient_repository.py`, `lead_repository.py`, etc. | dual filter | — | async, `get_by_id(*, tenant_id, clinic_id, user_id)` | active — **cablear (hoy `AsyncMock`)** |

### Decision por sistema

- **JWKS verifier (engine `auth.py:verify_token_payload`)** -> **EXTEND via import**. El decoder vitalia lo IMPORTA. NUNCA recrear `PyJWKClient`.
- **Role-from-DB (engine `dependencies.py:get_current_user`)** -> **REUSE conceptual, NO import directo del Depends sync**. Razon: el path engine es **sync** (`Session`) y resuelve por email; los routers PHI vitalia son **async** (`get_async_session`) y necesitan el rol dentro de `ClinicContext` (UUIDs tipados). Decision: el resolver vitalia resuelve el rol con una **query async brand-local minima** contra el model engine `UserTenantModel` (importado, NO mirroreado) filtrando `(user_id, tenant_id, is_active)`. Esto es **EXTEND** (consume el model engine + la logica de `verify_token_payload`), no NEW layer — no se crea un segundo JWKS ni un segundo `user_tenants`.
- **`user_tenants` model/repo (engine)** -> **REUSE via import** del `UserTenantModel`. El engine `UserTenantRepository` es sync y solo expone `get_tenants_for_user`; no sirve para el path async + lookup `(user,tenant)`. Por eso la query async vive brand-local consumiendo el **mismo model engine** (cero tabla nueva, cero mirror). Ver § Architecture Decisions AD-2.
- **stub decoder** -> **REPLACE in-place** (mantener `ClerkJwtPayload` shape + `ClerkJwtDecoder.decode` interfaz). Stub solo bajo `VITALIA_AUTH_STUB=1` + token `stub:` (test-only).
- **`ClinicResolver`/`ClinicContext`** -> **MODIFY**: el rol ya NO sale del payload; el resolver recibe el rol resuelto desde DB y lo pone en `ctx.role`. Interfaz `ClinicContext` (fields) intacta -> consumers (`ctx.role`) cero cambios.
- **`@require_phi_access` + `AuditLogRepository`** -> **REUSE tal cual** (no se toca).
- **repos PHI reales** -> **WIRE** (reemplazar `AsyncMock()` inline por instancias reales via `Depends(get_async_session)`).

**Conclusion:** cero NEW layer · cero mirror cross-brand · cero edit a `core/luana-core-*/src/`. Todo es EXTEND/REPLACE/WIRE sobre lo existente. Si durante el build se descubre que `verify_token_payload` necesita un cambio (no esperado) -> STOP + escalar `/pm-luana` (no editar engine).

---

## Prior art audit

- **Engine JWKS** (`core/luana-core-iam/application/auth.py`): consumido via import — cero recreacion.
- **Engine `user_tenants`** (`UserTenantModel`): consumido via import para la query de rol.
- **god-matrix fixture** (`vitalia/backend/scripts/seed_test_users_link.py`): reusado como fixture de verificacion (8 usuarios RBAC sobre Sanare).
- **cross-brand:** cero mirror (greps verbatim arriba). nicolify/comunify/lupulo no tienen `clerk_jwt_decoder.py` ni `clinic_resolver.py`.
- **`cap_change_type: extend`** coherente: el cap `iam-scaffold-slice-1` existe; esta story lo desentuba (stub -> JWKS real). NO crea cap.

---

## Integration design (CONN)

### Reachability path (como se LLEGA)

```
FE (AuditedSection.tsx) manda Authorization: Bearer <JWT real Clerk> + X-Tenant-ID + X-Clinic-ID
  -> router PHI (crm/marketing/inbox) construye ClinicResolver(decoder=ClerkJwtDecoder())
  -> decoder.decode(token):  VITALIA_AUTH_STUB!=1 (runtime) -> verify_token_payload(token) [engine JWKS]
                            -> extrae user_id = payload["sub"]
  -> resolver resuelve rol async desde user_tenants(user_id, tenant_id) [engine model] -> ClinicContext.role
  -> @require_phi_access(roles=[doctor,nurse,admin_clinic]) gatea + audit sync write
  -> repo PHI real (Depends get_async_session) dual-filter (tenant_id + clinic_id) -> data
  -> 200 + audit_log row  |  403 rol denegado  |  404 cross-tenant  |  401 JWT invalido
```

### Consumers (quien la USA)

- `ClerkJwtDecoder.decode` (JWKS real) -> consumido por `ClinicResolver` en crm/router, crm/consent_endpoints, marketing/deps + routes, inbox/router.
- Rol desde DB -> consumido por `@require_phi_access` (via `user_role=ctx.role`) en cada endpoint PHI.
- `GET /api/v1/iam/users/me` (rol context) -> consumido por FE `useCurrentUser` (1 fuente de verdad DB).

### Registration points (donde se CABLEA — deliverables verificables)

- BE: el decoder real ya esta notarizado (los routers lo instancian); el cambio es interno a `decode()`. Los repos reales se cablean en cada endpoint via `Depends(get_async_session)` (reemplaza `AsyncMock()` inline). NO se agrega router nuevo (engine `/me` ya montado en `main.py`).
- FE: `useCurrentUser` ya esta consumido por `RequireRole`/`usePiiRoleGate`; el cambio es la fuente (Clerk metadata -> `/me`). Cero ruta nueva.

### Home (cap)

- `cap_target: iam.iam-scaffold-slice-1` · `cap_change_type: extend` · dev_preview se actualiza al merge (scenarios SC-1..SC-4 + e2e_test path del integration test).

**NO isla:** el decoder real es Consumed (routers DI) + On-the-map (cap iam-scaffold) + Navigable (FE manda JWT real) + Notarized (wiring DI de cada router + engine /me montado).

---

## 1. Domain Entities

Sin entidades nuevas. Se preservan:

- `ClerkJwtPayload` (dataclass frozen, `vitalia/.../iam/infrastructure/clerk_jwt_decoder.py`) — shape intacto: `user_id, tenant_id, clinic_id, role, email, name`. **Nota:** post-Slice-2 el `role` del payload pierde autoridad (el rol real viene de DB); se mantiene el field para compat de shape, pero el resolver lo sobreescribe con el rol DB.
- `ClinicContext` (dataclass frozen, `iam/application/services/clinic_resolver.py`) — fields intactos: `user_id, tenant_id: UUID, clinic_id: UUID, role, email, name`. El `role` ahora proviene de DB.
- `VitaliaRole` (enum, `iam/domain/role.py`) + `PHI_ALLOWED_ROLES` — sin cambios.

## 2. SQLAlchemy 2.0 Models

Sin model nuevo. Se **consume via import** el model engine:

```python
from luana_core_iam.infrastructure.models.user_tenant_model import UserTenantModel
# columns: user_id (UUID PK FK users.id), tenant_id (UUID PK FK tenants.id), role (String), is_active (Boolean)
```

Query de rol (async, brand-local, SQLA 2.0):

```python
stmt = (
    select(UserTenantModel.role)
    .where(UserTenantModel.user_id == user_uuid)
    .where(UserTenantModel.tenant_id == tenant_uuid)
    .where(UserTenantModel.is_active.is_(True))
)
role: str | None = (await session.execute(stmt)).scalar_one_or_none()
```

> `user_uuid` se resuelve a partir de `payload["sub"]` (Clerk id string) -> buscar `users.clerk_id == sub` -> `users.id` (UUID). Reusar `UserModel` (import engine) para esa resolucion. Ver AD-2.

## 3. Pydantic v2 DTOs

Sin DTO nuevo en BE para el decoder. Para el FE role-context, **REUSAR el engine `/me`** que ya devuelve `User` (incluye `role`). Si el shape del engine `/me` no incluye `clinic`/`tenant` necesarios para el hook, exponer un DTO minimo brand-local solo-lectura (ver AD-3):

```python
class MeRoleContext(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: str
    role: str                # desde user_tenants.role (DB)
    tenant_id: str
    has_phi_access: bool
```

> Decision Q3-relacionada: si el engine `/me` ya basta para el FE -> NO crear DTO ni endpoint nuevo (consumir `/api/v1/iam/users/me` directo). El builder confirma en T-FE-hook leyendo el shape real del engine `/me` ANTES de decidir. Default: consumir engine `/me` (cero endpoint nuevo).

## 4. API Routes

No se agrega ruta BE nueva (engine `/me` ya montado). Las rutas PHI existentes (crm/marketing/inbox) mantienen contrato; solo cambia el wiring interno (repos reales). Todas conservan:

| Method | Path | Auth | response_model | Cambio |
|---|---|---|---|---|
| GET | `/api/v1/crm/patients/{id}` | Bearer + X-Tenant-ID + X-Clinic-ID | `PatientResponse` | repo real DI |
| PATCH | `/api/v1/crm/patients/{id}` | idem | `PatientResponse` | repo real DI |
| POST | `/api/v1/crm/patients/{id}/opt-out` | idem | (consent DTO) | repo real DI |
| PATCH | `/api/v1/crm/patients/{id}/marketing-opt-in` | idem | (consent DTO) | repo real DI |
| GET | `/api/v1/crm/leads` / `/leads/{id}` | idem | `LeadListResponse`/`LeadResponse` | repo real DI |
| GET | `/api/v1/crm/conversations*` | idem | conversation DTOs | repo real DI |
| GET/POST | `/api/v1/vitalia/marketing/*` | idem | (marketing DTOs) | rol desde DB en `verify_role` |
| POST/PATCH/GET | `/api/v1/vitalia/inbox/*` | idem | inbox DTOs | repo real DI ya parcial; rol desde DB |
| GET | `/api/v1/iam/users/me` | Bearer + X-Tenant-ID | `User` (engine) | **reuse** (FE consume) |

`redirect_slashes=False` ya en `main.py`.

## 5. TypeScript Types (Frontend)

`useCurrentUser` (`vitalia/frontend/src/hooks/useCurrentUser.ts`): el shape `CurrentUser` se mantiene; cambia la fuente:

```ts
// antes: const meta = user.publicMetadata; role = meta.role
// despues: React Query GET /api/v1/iam/users/me -> { role, ... }
interface CurrentUser {
  id: string; firstName: string | null; lastName: string | null;
  email: string | null;
  role: VitaliaRole | null;   // ahora desde /me (DB), no Clerk metadata
  hasPhiAccess: boolean;
  isLoaded: boolean;
}
```

> `useClinicId` (que tambien lee `publicMetadata.clinicId`) queda fuera de scope (clinic_id sigue desde header `X-Clinic-ID` que el FE ya manda). Solo el ROL migra a `/me`.

## 6. Repository Interfaces

Sin interfaz nueva. Se reusan async, tenant+clinic scoped:

- `PatientRepository(session, audit_repo).get_by_id(entity_id, *, tenant_id, clinic_id, user_id)` — ya existe.
- `LeadRepository`, `ConversationRepository`, `MessageRepository`, `ActivityEventRepository`, `ActionReceiptRepository` — ya existen (hoy mockeados en algunos paths).
- `AuditLogRepository(session).write(AuditLogEntry)` — ya existe (async, sync-awaited).

Sub-scope a confirmar en build (Q3): el builder verifica que cada repo real exista antes de cablear. Si alguno falta para un endpoint concreto -> marcar sub-scope explicito en `T-*-impl-log.md` (NO inventar repo nuevo).

## 7. Application Services

- `ClinicResolver.resolve(token)` -> ahora **async** o recibe el rol resuelto: el resolver delega JWKS al decoder, extrae `user_id`, resuelve `role` desde DB (query § 2), construye `ClinicContext` con ese rol. Transaccion: read-only para resolucion de rol; el audit write sync lo hace `@require_phi_access`.
- Idempotencia: N/A (reads PHI + audit append-only; consent POST ya usa idempotency key existente).

## 8. Agentic Surfaces

**N/A** — esta story no toca `copilot` ni `sales_agent`. Sin LangGraph/tools/prompt-slots/goldens.

## 9. Migration Notes

**Sin migracion** — `user_tenants` ya existe (engine), audit_log table ya existe (vitalia). Cero DDL. (El seed `seed_test_users_link.py` ya poblo la god-matrix.)

## 9.5 Tests audit (default flip)

- [x] **No aplica — CONTRACT no flipea defaults side-effect.** `VITALIA_AUTH_STUB` es env test-only que por defecto NO existe en runtime; introducirlo en tests no flipea un default de produccion (el default de produccion es "sin env -> JWKS real", que es el comportamiento target). El arch test `test_auth_stub_env_gate.py` enforce que runtime/dev config nunca lo setean.

## 10. File Structure

```
vitalia/backend/src/modules/vitalia/
|- iam/
|  |- infrastructure/clerk_jwt_decoder.py          [MODIFIED] decode(): JWKS real via verify_token_payload; stub solo VITALIA_AUTH_STUB=1
|  \- application/services/clinic_resolver.py       [MODIFIED] rol desde DB (query user_tenants async); ClinicContext shape intacto
|- crm/api/router.py                                 [MODIFIED] repos reales DI (quita AsyncMock inline)
|- crm/api/consent_endpoints.py                      [MODIFIED] repos reales DI
|- marketing/api/deps.py + routes.py                 [MODIFIED] verify_role/get_clinic_context rol desde DB
\- inbox/api/router.py                               [MODIFIED] repos reales DI (parcial ya) + rol desde DB
vitalia/backend/tests/
|- integration/test_phi_real_auth.py                 [NEW] SC-1..SC-4
\- architecture/test_auth_stub_env_gate.py           [NEW] runtime no setea VITALIA_AUTH_STUB
vitalia/frontend/src/hooks/useCurrentUser.ts          [MODIFIED] rol desde GET /api/v1/iam/users/me
```

## 11. Cross-Cutting Concerns

- **Tenant isolation:** la query de rol filtra `(user_id, tenant_id, is_active)`. Toda query PHI dual-filter `tenant_id + clinic_id` (ya enforced por `PhiRepositoryBase`).
- **HIPAA-lite (overlay):** dual filter + audit sync pre-response + sanitization en traces + `@require_phi_access(roles=[doctor,nurse,admin_clinic])`. Cross-tenant -> 404 (no leak), cross-clinic -> 403.
- **Currency/master-data:** N/A (sin monetary/datetime nuevos).
- **Spanish neutro:** errores user-facing 401/403 en espanol neutro ("Token invalido o expirado.", "Acceso denegado: tu rol no tiene permisos para acceder a informacion clinica."). Ya presentes — preservar.
- **PII:** `response_model=` en cada endpoint (ya enforced); el `/me` engine devuelve `User` sin PHI.
- **Native-first:** tests corren native (`${WS}/.venv/bin/pytest`), nunca docker exec.

## 12. Architecture Fitness Impact

- Gates que corren: `test_phi_dual_filter.py`, `test_audit_log_sync_write.py`, `test_audit_log_row_per_phi_endpoint.py`, `test_response_model_required.py`, `test_no_phi_in_url_params.py` (deben seguir verdes) + **NUEVO** `test_auth_stub_env_gate.py`.
- Allowlists: no crecen. El reemplazo del stub + wiring real elimina los `AsyncMock` inline (deuda) -> mejora.

## 13. capability YAML + modules/{m}.md Updates Required

- `vitalia/docs/product/capabilities/iam/iam-scaffold-slice-1.yaml`: append `change_log` (`type: extend`, story id, fecha) + scenarios SC-1..SC-4 con `added_in_story` + `e2e_test: vitalia/backend/tests/integration/test_phi_real_auth.py::...`. `last_modified` = 2026-05-30.
- `vitalia/docs/product/modules/iam.md`: si narrativa cambia (auth real vs stub) — auto-block reconcile.

## 14. Test Surfaces (TDD-mandatory)

- **BE domain/infra/app:** RED — resolver de rol desde DB (unit: `(user_id,tenant_id)` -> role); decoder JWKS-vs-stub gate (unit con `VITALIA_AUTH_STUB`).
- **BE integration:** `test_phi_real_auth.py` SC-1..SC-4 (ver 04-validators `scenario_coverage`).
- **BE arch:** `test_auth_stub_env_gate.py` (RED: runtime config no contiene `VITALIA_AUTH_STUB`).
- **FE hook:** Vitest — `useCurrentUser` lee rol desde `/me` (success/loading/error); RED antes.
- **E2E/manual:** god-matrix con JWT real (mint Clerk Backend API) — gate de verificacion supervisado.

## 15. Research Notes (date-aware)

- **Sin research externo.** Todo el contrato se resuelve consumiendo engine `core/luana-core-iam` ya presente in-repo (leido 2026-05-30): `application/auth.py::verify_token_payload`, `api/dependencies.py::get_current_user/get_user_from_token`, `infrastructure/models/user_tenant_model.py`. Opus 4.8 cutoff Jan 2026 no aplica — la fuente de verdad es el codigo del repo, no conocimiento del modelo.
- PyJWT JWKS pattern (`PyJWKClient`, RS256, leeway): ya implementado en engine; no se re-investiga ni se reimplementa.

## 16. Open Questions for PM

- **OQ-1 (Q3 — sub-scope repos):** El builder DEBE confirmar en T-repos-wire que existen repos reales para TODOS los endpoints PHI de crm/consent/marketing/inbox. Si algun endpoint no tiene repo real disponible -> marcar sub-scope explicito en `T-repos-wire-impl-log.md` (NO inventar repo nuevo). Evidencia esperada: lista endpoint->repo real.
- **OQ-2 (FE `/me` shape):** El engine `GET /api/v1/iam/users/me` (devuelve `User` con `role` resuelto por `X-Tenant-ID`) basta para el hook FE, o el FE necesita `has_phi_access` calculado server-side? Default: consumir engine `/me` directo (el FE calcula `hasPhiAccess` con el set de roles PHI que ya tiene). Si se requiere endpoint brand-local -> marcar en impl-log (cero edit engine).

## Architecture Decisions

- **AD-1 (adr_004_compliance: n/a-with-rationale):** ADR-vitalia-004 aplica a stories que construyen **sub-tab UI nueva** dentro del shell-organism. Esta story es **BE-auth wiring + 1 hook FE** (NO sub-tab, NO route group nuevo, NO componente shell nuevo). Por eso `n/a-with-rationale`: no hay UI sub-tab que cumplir las 9 secciones. El unico cambio FE (rol desde `/me`) es a un hook existente, no a una vista de sub-tab.
- **AD-2 (rol DB query async brand-local, no engine repo):** el engine `UserTenantRepository` es sync (`Session`) y solo expone `get_tenants_for_user`. Los routers PHI vitalia son async. Reusar el Depends sync del engine (`get_current_user`) dentro del path async romperia el modelo. Decision: query async brand-local **consumiendo el model engine `UserTenantModel`** (import, cero tabla/mirror). Esto es EXTEND, no NEW. Resolucion `sub` (Clerk string) -> `users.id` (UUID) via `UserModel.clerk_id` (import engine `UserModel`).
- **AD-3 (FE consume engine `/me`, no endpoint brand nuevo):** default = consumir `/api/v1/iam/users/me` (ya montado, devuelve role-from-DB). Solo crear DTO/endpoint brand-local si el shape engine no basta (OQ-2). Evita NEW layer.
- **AD-4 (stub env-gated, Q2):** `ClerkJwtDecoder.decode`: `if os.environ.get("VITALIA_AUTH_STUB")=="1" and token.startswith("stub:") -> _decode_stub` ; else -> `verify_token_payload(token)` + map payload a `ClerkJwtPayload`. Runtime/dev-app nunca setean la env -> siempre JWKS real. Arch test enforce.
