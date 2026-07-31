---
slug: admin-iam-adoption-platform
kind: outcome
owner: /pm-luana
state: refining
created: 2026-05-19
priority: HIGH
why_now: |
  Vitalia auth-base-functional cerró state=done sin que admin Streamlit fuese realmente
  ejercitado durante validators. Smoke post-merge reveló que admin tenants.py + users.py
  hacen SQL a tablas phantom (vitalia_clinics, vitalia_user_profiles, vitalia_tenants)
  que NO existen en ninguna migration vitalia. Causa raíz: vitalia reinventó el modelo
  IAM en lugar de consumir luana-core-iam que YA existe (44 .py + 14 tests, modelos
  User/Tenant/UserTenant completos + Clerk JWT verification + webhook sync + repos).
  Sin fix: (a) admin no funciona, (b) violación anti-duplication rule, (c) cuando vengan
  los 6 brands futuros (saasora/inmoflow/retailly/fixia/guestly/fitflow) hay riesgo
  alto de repetir el error si no documentamos el patrón canónico ahora.
estimated_effort: 8-12h cross-brand (1-2h /pm-luana proposal + 4-6h /pm-vitalia adopción + 2-4h config purge engine + 1h hardcodes residuales lift)
stories:
  - S-PLATFORM-PURGE-NICOLIFY-DEFAULTS-CORE-CONFIG     # ✅ MIGRATED b869eaf (proposal padre)
  - S-PLATFORM-PURGE-NICOLIFY-HARDCODES-RESIDUALES     # ✅ MIGRATED 39b73703 (sales-agent + copilot + llm broadened scope)
  - S-VITALIA-ADOPT-LUANA-CORE-IAM                     # ⏳ /pm-vitalia handed off (next session)
related_proposals:
  - docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-defaults-core-config.md (state=migrated, commit b869eaf)
  - docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-hardcodes-sales-agent.md (state=migrated, commit 39b73703 — broadened scope sales-agent + copilot + llm)
related_rules:
  - .claude/rules/anti-duplication.md (§ lift shared rule — base del cross-brand mirror detection)
  - vitalia/.claude/rules/hipaa-lite.md (dual filter tenant_id + clinic_id obligatorio)
---

# Admin + IAM adoption — platform outcome

> Outcome owned por `/pm-luana`. Cubre 3 problemas relacionados que afectan vitalia HOY pero
> que también marcan el patrón canónico para todas las brands futuras (10 universos total).

## Problema (3 manifestaciones)

### P1 — Vitalia admin code es phantom

`vitalia/backend/src/modules/vitalia/admin/modules/tenants.py` + `users.py` hacen SQL crudo
a tablas que NO existen:
- `vitalia_clinics` — sin CREATE TABLE en ninguna de las 21 migrations vitalia
- `vitalia_user_profiles` — idem
- `vitalia_tenants` — idem (canónica es `tenants` engine sin prefix)

Resultado: admin login falla en `(psycopg2.errors.UndefinedTable) relation "vitalia_clinics" does not exist`
después de validar bcrypt password OK.

### P2 — Engine ya tiene el modelo IAM correcto pero está siendo ignorado

`core/luana-core-iam/` (post 1-semana de carve-out 2026-05-15) tiene **todo el modelo IAM
brand-agnostic completo**:

| Componente | Path | Estado |
|---|---|---|
| `UserModel` (users) | `core/luana-core-iam/src/luana_core_iam/infrastructure/models/user_model.py` | ✅ Completo |
| `TenantModel` (tenants) | `…/infrastructure/models/tenant_model.py` | ✅ Completo |
| `UserTenantModel` (user_tenants M:N + role per tenant) | `…/infrastructure/models/user_tenant_model.py` | ✅ Completo |
| `verify_clerk_token()` JWT RS256 + JWKS | `…/application/auth.py:64` | ✅ Implementado |
| Clerk webhook handler (user.created/updated/deleted) | `…/api/webhooks.py:87` | ✅ Implementado |
| `UserRepository` + `TenantRepository` + `UserTenantRepository` | `…/infrastructure/repositories/` | ✅ CRUD |
| `UserService` + `TenantService` | `…/application/services/` | ✅ Business logic |
| `get_current_user()`, `get_current_tenant_id()` Depends | `…/api/dependencies.py` | ✅ FastAPI-ready |
| `tenant_router.py` CRUD tenants | `…/api/` | ✅ Endpoints |
| Tests | `core/luana-core-iam/tests/` (14 archivos) | ✅ Coverage |

Nicolify (brand origen del carve-out) consume este engine correctamente: `nicolify/backend/alembic/versions/001_initial_snapshot.py:2210,2255,2264`
crea `CREATE TABLE users`, `CREATE TABLE tenants`, `CREATE TABLE user_tenants` matching engine models.

Vitalia migration 001 **olvidó** crear esas 3 tablas — solo creó las 11 tablas medical.

### P3 — Engine `core/luana-core-platform/core/config.py` contiene hardcodes Nicolify

4 defaults brand-specific contaminan el engine cross-brand:

| Línea | Variable | Valor hardcoded | Brand leak |
|---|---|---|---|
| L48 | `FRONTEND_URL` | `"https://app.nicolify.com"` | nicolify domain |
| L45 | `COPILOT_TELEGRAM_BOT_USERNAME` | `"nicolify_copilot_bot"` | nicolify bot |
| L185 | `QDRANT_COLLECTION` | `"visionarias_knowledge"` | nicolify legacy name |
| L240 | `LITELLM_BASE_URL` | `"http://visionarias_litellm:4000/v1"` | nicolify container name |

Cuando vitalia (o cualquier otra brand) consume el core sin override `.env` explícito,
hereda defaults Nicolify. Riesgo: data mixing (vitalia escribe a Qdrant collection Nicolify),
roto LLM proxy, frontend redirects mal, copilot Telegram con bot equivocado.

## Decisión arquitectónica ratificada (Chris 2026-05-19)

### D1 — Vitalia consume `luana-core-iam` (no reinventa)

`vitalia/backend/alembic/versions/001_vitalia_initial_snapshot.py` debe agregar:

```sql
CREATE TABLE IF NOT EXISTS users (...);          -- matching luana_core_iam.UserModel
CREATE TABLE IF NOT EXISTS tenants (...);        -- matching luana_core_iam.TenantModel
CREATE TABLE IF NOT EXISTS user_tenants (...);   -- matching luana_core_iam.UserTenantModel
```

Mismo schema que nicolify (auditable via `nicolify/backend/alembic/versions/001_initial_snapshot.py:2210-2300`).
Patrón canónico: **engine define ORM models (SSoT), cada brand ejecuta DDL en su migration**.

Vitalia admin code se REESCRIBE consumiendo:
- `UserRepository.create()` / `.get_by_clerk_id()` / `.update()`
- `TenantRepository.create()` / CRUD
- `UserTenantRepository.link(user_id, tenant_id, role)`
- `verify_clerk_token()` para auth (futuro Slice 2)

Cero SQL crudo. Cero tabla phantom. Cero violación anti-duplication rule.

### D2 — Concept `clinic` = brand-extension vitalia (NO engine)

Vitalia introduce sub-unidad organizacional `clinic` (vertical médico — clínica física con
dirección, equipo, RBAC PHI scoped). Relación: **`tenant 1—N clinic`**.

- Engine NO conoce clinic concept (otras brands no lo necesitan ahora: nicolify=agency flat, comunify=creator flat)
- Vitalia agrega tabla `vitalia_clinics` con FK a `tenants.id` (engine table)
- Vitalia HIPAA-lite rule (`vitalia/.claude/rules/hipaa-lite.md`) refuerza dual filter `tenant_id + clinic_id` en TODA query PHI
- Si en futuro 2da brand (lupulo=restaurant_location, fitflow=gym_location, guestly=property_location, fixia=service_area, retailly=warehouse) replica el patrón → **trigger automático para lift EP-19 `TenantSubUnit`** a engine (per promotion protocol)

Anti-pattern explícito: no crear `vitalia_clinics` HOY como engine-level por especulación.
**Brand-first, core-second.** Una brand activa NO justifica lift; pasamos por promotion gate cuando 2da brand lo necesite.

### D3 — Hardcodes Nicolify en core/config.py → PURGE ✅ MIGRATED

Ver `docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-defaults-core-config.md`
(state=migrated, commit `b869eaf`). Defaults cambiados a strings vacíos. Brand consumidora DEBE
override en `.env.dev` / `.env.prod`. Sin override → `RuntimeError` explícito (fail fast).

### D3.bis — Hardcodes Nicolify residuales en sales-agent + copilot + llm → PURGE ✅ MIGRATED

Ver `docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-hardcodes-sales-agent.md`
(state=migrated, commit `39b73703`). **Pre-requisite paso previo cementado en esta sesión** post
descubrimiento del auditor-backend WARN INFO-2 del lift padre + Chris "bug free total" directive.

Cambios:
- `core/luana-core-sales-agent` 0.1.0 → 0.2.0: helper `_build_payment_url()` deriva success/cancel
  URLs Stripe desde `settings.FRONTEND_URL` (failfast empty) + remove deprecated header
  `x-nicolify-tenant-id` fallback (standard `x-tenant-id` only)
- `core/luana-core-copilot` 0.1.0 → 0.2.0: refactor `_TELEGRAM_CHANNEL_CONTEXT_ES` const a
  template + lazy helper `_get_telegram_channel_context_es()` con cache. Resuelve `@__TELEGRAM_BOT__`
  y `__FRONTEND_DOMAIN__` desde settings (preserva Anthropic/Kimi prompt cache invariant).
  **FIXES FUNCTIONAL BUG:** agent vitalia/comunify/lupulo previamente decía a usuarios "vayan a
  app.nicolify.com" cross-brand (UX broken + posible data leak).
- `core/luana-core-llm` (no bump, docstring only): comentario brand-agnostic en `litellm.py`.

Behavioral verify pre-merge: nicolify behavior **BYTE-IDENTICAL** (defaults derivan via env
override a mismos valores hardcoded). vitalia/comunify/lupulo ahora correctamente brand-agnostic.

### D4 — Admin Streamlit per-brand con puerto dedicado

Mismo patrón que frontend ports (3001/3002/3003/3004) y backend ports (8001/8002/8003/8004):

| Brand | Admin port | Container name |
|---|---|---|
| nicolify | 8501 | luana-{env}-nicolify_admin-1 |
| vitalia | 8502 | luana-{env}-vitalia_admin-1 |
| comunify | 8503 | luana-{env}-comunify_admin-1 |
| lupulo | 8504 | luana-{env}-lupulo_admin-1 |
| saasora | 8505 | luana-{env}-saasora_admin-1 |
| inmoflow | 8506 | luana-{env}-inmoflow_admin-1 |
| retailly | 8507 | luana-{env}-retailly_admin-1 |
| fixia | 8508 | luana-{env}-fixia_admin-1 |
| guestly | 8509 | luana-{env}-guestly_admin-1 |
| fitflow | 8510 | luana-{env}-fitflow_admin-1 |

Cada brand agrega service `{brand}-admin` a su `{brand}/docker-compose.dev.yml` exponiendo
puerto correspondiente. Patrón ya documentado en `docs/portfolio/INFRA-MATRIX.md` para FE/BE,
extender a Admin column. Brand-config en `{brand}/config/brand.yaml::infra.admin_port`.

### D5 — Admin = super-CRUD interno (Chris only, NO clientes)

Confirmado: admin es para Chris solo. Funcionalidades canónicas:
- Crear tenants (clientes) + asignar plan_tier
- Crear usuarios + asignar a 1+ tenants via `user_tenants` (role per tenant)
- Banear usuario global (toggle `users.is_active`)
- Suspender tenant (toggle `tenants.is_active`)
- Ver consumo LLM por tenant (consume `core/luana-core-observability/` reports)
- Marcar pagos manuales (futuro, when billing module madura)
- Monitor + observabilidad (NO superpoderes runtime — auditable read-only)

Auth admin: bcrypt single super-admin password (`{BRAND}_ADMIN_PASSWORD_HASH` env var).
NO Clerk (admin no es flow Clerk customer-facing).
Documentar este pattern como ADR para no reabrir el debate cuando lleguen las 6 brands futuras.

## Sub-outcomes y stories

### S-PLATFORM-PURGE-NICOLIFY-DEFAULTS-CORE-CONFIG ✅ MIGRATED 2026-05-19 (commit b869eaf)

Owner: `/pm-luana` (proposal) + autonomous lift cycle
Estimado real: 2h
Artifacts: `docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-defaults-core-config.md`

Cambios ejecutados:
- 4 defaults purgados en `core/luana-core-platform/core/config.py`: FRONTEND_URL,
  COPILOT_TELEGRAM_BOT_USERNAME, QDRANT_COLLECTION, QDRANT_COLLECTION_HYBRID, LITELLM_BASE_URL
- CHANGELOG `core/luana-core-platform/CHANGELOG.md` entry 0.3.0 (minor bump)
- `nicolify/.env.dev` + `vitalia/.env.dev` + `comunify/.env.dev` pre-set con valores explícitos
- `{nicolify,vitalia,comunify,lupulo}/.env.dev.template` updated con "Brand-specific config" block
- R3 downstream regression PASS (engine + 4 brand consumers)
- `core/luana-core-platform/pyproject.toml::version` 0.2.0 → 0.3.0

### S-PLATFORM-PURGE-NICOLIFY-HARDCODES-RESIDUALES ✅ MIGRATED 2026-05-19 (commit 39b73703)

Owner: `/pm-luana` autonomous lift cycle (post auditor WARN-1 + Chris "bug free total")
Estimado real: 1.5h (broadened scope iter 2)
Artifacts: `docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-hardcodes-sales-agent.md`

Cambios ejecutados (3 engine packages):
- `core/luana-core-sales-agent` 0.1.0 → 0.2.0: providers.py helper `_build_payment_url()` +
  payment_webhooks.py remove `x-nicolify-tenant-id` header fallback + CHANGELOG.md created
- `core/luana-core-copilot` 0.1.0 → 0.2.0: graph.py refactor const → template + lazy helper
  `_get_telegram_channel_context_es()` con cache (FIXES functional bug: agent vitalia decía
  "vayan a app.nicolify.com") + telegram_redirect.py docstring brand-agnostic + CHANGELOG.md created
- `core/luana-core-llm` (no bump): litellm.py docstring brand-agnostic
- Gate-runner iter 2: copilot 1640 PASS + orchestrator 19 PASS + llm PASS + ruff PASS +
  platform regression PASS. Sales-agent ADVISORY_PRE_EXISTING (verified against base commit).

### S-VITALIA-ADOPT-LUANA-CORE-IAM (jurisdicción /pm-vitalia)

Owner: `/pm-vitalia` (outcome local + spec story) + `/dev-team` (implementación)
Estimado: 4-6h
Artifacts: `vitalia/docs/product/outcomes/admin-iam-adopt.md` + 1 story bajo el outcome

Sub-tasks de la story:

1. **Migration agregar tablas engine en vitalia_dev** (T-be-add-engine-iam-tables)
   - Nueva migration `022_vitalia_add_engine_iam_tables.py` o EDITAR 001 snapshot
   - `CREATE TABLE IF NOT EXISTS users` matching `luana_core_iam.UserModel`
   - `CREATE TABLE IF NOT EXISTS tenants` matching `luana_core_iam.TenantModel`
   - `CREATE TABLE IF NOT EXISTS user_tenants` matching `luana_core_iam.UserTenantModel`
   - Tomar shape verbatim desde `nicolify/backend/alembic/versions/001_initial_snapshot.py:2210-2300` (proven canonical)

2. **Aplicar 12 migrations pending 002-013** (T-be-apply-pending-migrations)
   - Hoy DB vitalia_dev está en `001_vitalia`. Hay 12 migrations no aplicadas.
   - `docker exec luana-dev-vitalia_backend_dev-1 alembic upgrade head` después del Step 1
   - Migration 014+ (tenants location columns) ahora será aplicable (tabla `tenants` existe post Step 1)

3. **Reescribir admin code consumiendo engine** (T-be-admin-rewrite + T-be-admin-deletion)
   - **DELETE** queries SQL crudas en `vitalia/backend/src/modules/vitalia/admin/modules/tenants.py`
   - **DELETE** queries SQL crudas en `vitalia/backend/src/modules/vitalia/admin/modules/users.py`
   - **REWRITE** consumiendo `UserRepository`, `TenantRepository`, `UserTenantRepository` del engine
   - DELETE cualquier import / helper / stub que apunte a tablas phantom
   - Cero deuda técnica residual (per directiva Chris 2026-05-19)

4. **Agregar tabla brand-extension vitalia_clinics** (T-be-clinics-extension)
   - Nueva migration con `CREATE TABLE vitalia_clinics` + FK `tenant_id REFERENCES tenants(id)`
   - SQLAlchemy model en `vitalia/backend/src/modules/vitalia/clinics/infrastructure/models/clinic_model.py`
   - Repository + service
   - Admin page `clinics.py` (read + create + assign user-to-clinic)
   - HIPAA-lite dual filter helper `@require_clinic_access(...)` reforzando rule

5. **Service vitalia-admin docker-compose puerto 8502** (T-infra-admin-service)
   - Agregar service `vitalia-admin` a `vitalia/docker-compose.dev.yml`
   - `ports: ["127.0.0.1:8502:8501"]`
   - `command: streamlit run src/modules/vitalia/admin/app.py --server.port=8501`
   - Update `vitalia/config/brand.yaml::infra.admin_port: 8502`
   - Re-gen `docs/portfolio/INFRA-MATRIX.md` via `make infra-matrix`

6. **Update Makefile target `make dev-vitalia-admin`** (T-infra-makefile)
   - Target wrapper levantando solo el admin service (mismo patrón frontend/backend)

7. **Eliminar Bug #1 origen — fix `.env.dev.template`** (T-doc-env-template)
   - Agregar comentario en `vitalia/.env.dev.template` explicando single-quote para valores con `$`/`!`/espacios
   - Caso paradigma: `VITALIA_ADMIN_PASSWORD_HASH='$2b$12$...'` (bcrypt hashes)

### Futuro EP-19 `TenantSubUnit` (trigger automático cuando 2da brand lo necesite)

NO ejecutar ahora. Vigilar promotables-scan cuando alguna de estas brands implemente sub-unit:
- lupulo: restaurant_locations (multi-sede restaurant chain)
- fitflow: gym_locations (multi-sede gimnasios)
- guestly: properties (multi-property hotel/B&B)
- fixia: service_areas (zonas técnico per-tenant)
- retailly: warehouses (multi-warehouse fulfillment)

Cuando 2da brand replique patrón → `/pm-luana` abre proposal lift `tenant_sub_units` table
generalizada en `core/luana-core-iam/` con EP-19 contract.

## Success criteria

- [ ] Vitalia admin login + tenant listing + user listing funciona contra DB real (cero phantom queries)
- [ ] Cero SQL crudo en `vitalia/backend/src/modules/vitalia/admin/` (todo via engine repos)
- [ ] Tabla `vitalia_clinics` existe con FK válida a `tenants` engine
- [ ] HIPAA-lite dual filter test cross-clinic bloqueado (per `vitalia/.claude/rules/hipaa-lite.md` §Tests requeridos)
- [ ] Admin Streamlit accesible en `http://127.0.0.1:8502` (puerto dedicado vitalia, no forwarder)
- [ ] `core/luana-core-platform/core/config.py` sin defaults nicolify-specific (4 hardcodes purgados)
- [ ] Arch fitness R3 GREEN en engine + 4 brands shipped post merges
- [ ] `vitalia/.env.dev.template` documenta single-quote requirement
- [ ] Capabilities updated: `vitalia/docs/product/capabilities/admin/` + `vitalia/docs/product/capabilities/iam/`
- [ ] Aprendizaje cementado en `.claude/skills/pm-luana/references/brand-bootstrap-learnings.md` (anti-pattern catalogado para futuras 6 brands)

## Anti-patterns prohibidos (cement para 6 brands futuras)

Estos errores **NO se vuelven a cometer** al bootstrap saasora/inmoflow/retailly/fixia/guestly/fitflow:

1. ❌ **Reinventar tablas users/tenants/user_tenants por brand.** Engine `luana-core-iam` ya las define. Cada brand SOLO ejecuta `CREATE TABLE` en su migration 001 con el schema canónico (copy verbatim desde nicolify 001 o referencia explícita a `luana_core_iam.{User,Tenant,UserTenant}Model`).

2. ❌ **SQL crudo en admin code apuntando a tablas brand-prefixed (vitalia_users, comunify_tenants, etc.)** — Admin SIEMPRE consume engine services (`UserRepository`, `TenantRepository`, `UserTenantRepository`).

3. ❌ **Hardcoded brand-specific defaults en `core/luana-core-*/`** — todo lo que difiere por brand vive en `{brand}/.env.dev` o `{brand}/config/brand.yaml`. Engine packages tienen defaults vacíos o `ConfigError` explícito.

4. ❌ **Skip migration apply post-bootstrap.** Cada brand al bootstrap debe correr `alembic upgrade head` en su DB ANTES de empezar features. Caso vitalia: estuvo en `001_vitalia` con 20 migrations pendientes — admin smoke nunca corrió.

5. ❌ **Crear sub-unit organizational table (clinic/location/property/area/warehouse) directamente en engine sin promotion proposal.** Brand-first siempre. Cuando 2da brand lo replique → proposal EP-19 + lift formal.

6. ❌ **Cerrar story state=done sin haber ejercitado admin smoke end-to-end (login + CRUD básico).** Validators deben cubrir admin path si la story incluye admin scaffold.

7. ❌ **Cross-brand mirror del módulo admin (copiar `nicolify/backend/.../admin/` → `vitalia/backend/.../admin/` con renames).** Cuando 2da brand replique admin idéntico → proposal lift `luana-core-admin` con extension SDK EP-N para brand-specific pages.

## Trazabilidad

- Caso origen: `vitalia/docs/product/stories/vitalia-auth-base-functional/HANDOFF-next-session.md` (4 bugs admin Streamlit descubiertos post-merge)
- Investigation chain: `vitalia/docs/product/stories/vitalia-auth-base-functional/` state=done sin admin smoke ejercitado
- Engine reference: `core/luana-core-iam/` (carve-out semana 2026-05-08..15, 44 .py + 14 tests)
- Architecture context: `docs/architecture/luana-platform/01-core-audit.md` + `02-core-purge-audit.md` + `03-nicolify-carve-out-audit.md`
- Related rule: `.claude/rules/anti-duplication.md` § lift shared rule
- Related rule: `.claude/rules/auditor-downstream-regression.md` § engine edit detection
- Related ADR: `vitalia/docs/architecture/ADR-vitalia-001-shared-vs-fork.md` (vitalia hereda core sin fork — coherente con esta decisión)

## Bitácora

- 2026-05-19: outcome opened by /pm-luana post Chris ratificación 4 decisiones (D1-D4) + D5 super-CRUD interno
  cementado. Bug origen: vitalia-auth-base-functional admin Streamlit smoke phantom tables. State: refining.
