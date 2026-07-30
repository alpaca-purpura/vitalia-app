# Brand Bootstrap — Learnings y Anti-patterns Catalogados

> Reference doc del skill `/pm-luana` (carga on-demand cuando user dice "bootstrap brand X").
> SSoT consolidado de errores observados + patrón canónico ratificado para los 6 brands pendientes bootstrap:
> **saasora, inmoflow, retailly, fixia, guestly, fitflow**.

**Origen del file:** 2026-05-19, post incidente vitalia-auth-base-functional donde admin Streamlit se rompió post-merge porque vitalia reinventó modelo IAM en lugar de consumir `luana-core-iam` que ya existía.

---

## Filosofía cardinal

> **"Si el engine ya lo tiene, NO lo reinventes en la brand. Si no lo tiene y necesitás algo brand-específico, escríbelo en `{brand}/` con escope brand-extension. Si después una 2da brand replica el patrón → promotion proposal lift al engine."**

Esto es el cement del principio **brand-first, core-second** de `docs/promotion-protocol/README.md` combinado con la regla anti-duplication. NO hay atajos.

---

## Patrón canónico bootstrap brand nueva (saasora/inmoflow/retailly/fixia/guestly/fitflow)

Cuando Chris dice "bootstrap brand {slug}" o "comenzá brand X", el patrón obligatorio es:

### Step 0 — Pre-bootstrap audit cross-engine

ANTES de crear cualquier código brand, auditar QUÉ del engine ya cubre los flujos esperados de la brand nueva:

```bash
WS=$(git rev-parse --show-toplevel)
# 1. Lista 26 packages engine
ls ${WS}/core/luana-core-*/

# 2. Lee README de cada package relevante para los flujos brand (IAM, billing, scheduling, etc.)
cat ${WS}/docs/core-modules/README.md
cat ${WS}/docs/core-modules/iam.md
cat ${WS}/docs/core-modules/platform.md
cat ${WS}/docs/core-modules/billing.md  # if billing relevant para vertical
# etc.

# 3. Inspect SQLAlchemy models en engine
ls ${WS}/core/luana-core-iam/src/luana_core_iam/infrastructure/models/
ls ${WS}/core/luana-core-platform/src/luana_core_platform/

# 4. Lee proposals migradas — qué ya se LIFTED al core
ls ${WS}/docs/promotion-protocol/proposals/ | xargs -I{} grep -l "state: migrated" {}
```

Output: lista explícita de QUÉ models/services/contracts engine cubre + QUÉ falta crear como brand-extension.

### Step 1 — Scaffold brand desde `_pm-sistema-template/`

```bash
cp -r ${WS}/.claude/skills/_pm-sistema-template ${WS}/.claude/skills/pm-{slug}
# Editar pm-{slug}/SKILL.md reemplazando placeholders {BRAND}
mkdir -p ${WS}/{slug}/{backend,frontend,deploy,config,docs}/
mkdir -p ${WS}/{slug}/docs/product/{outcomes,stories,capabilities,modules}/
mkdir -p ${WS}/{slug}/docs/{learnings,architecture,domains}/
mkdir -p ${WS}/{slug}/.claude/{rules,skills}/
mkdir -p ${WS}/{slug}/backend/src/modules/{slug}/
mkdir -p ${WS}/{slug}/backend/alembic/versions/
```

### Step 2 — Brand config + .env templates

```bash
# {slug}/config/brand.yaml
cat > ${WS}/{slug}/config/brand.yaml <<EOF
brand: {slug}
vertical: {Vertical descriptor}
compliance_level: {standard|hipaa_lite|pci|...}
enabled_sections:
  - identity
  - positioning
  # ... per /pm-luana decisión
preset_pack: {slug}_default
infra:
  backend_port: 80{XX}      # nicolify=01, vitalia=02, comunify=03, lupulo=04, saasora=05, etc.
  frontend_port: 30{XX}
  admin_port: 85{XX}        # NUEVO: per outcome admin-iam-adoption 2026-05-19
  db_name: {slug}_dev
  redis_db: {N}             # incremental per brand
  qdrant_prefix: {slug}_
EOF

# {slug}/.env.dev.template (con bloque brand-specific config CANÓNICO)
cat > ${WS}/{slug}/.env.dev.template <<EOF
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@luana-dev-luana_postgres_dev-1:5432/{slug}_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB={slug}_dev

# Clerk auth (brand tiene su propia Clerk app — registrar en dashboard.clerk.com)
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...

# Brand-specific config (engine consume desde aquí, REQUIRED override per brand)
# Post outcome admin-iam-adoption 2026-05-19 — engine defaults son "", brand DEBE setear.
FRONTEND_URL=https://dev-app.{slug}lat.com           # production frontend domain
COPILOT_TELEGRAM_BOT_USERNAME={slug}_copilot_bot     # registrar Bot por brand en BotFather
QDRANT_COLLECTION={slug}_knowledge                   # Qdrant collection per brand (DATA ISOLATION CRÍTICO)
QDRANT_COLLECTION_HYBRID={slug}_hybrid               # Qdrant hybrid search per brand
LITELLM_BASE_URL=http://luana-dev-{slug}_litellm-1:4000/v1   # LiteLLM proxy container per brand

# Admin Streamlit auth (bcrypt single super-admin password)
{SLUG}_ADMIN_PASSWORD_HASH='$2b$12$...'              # ⚠ single-quote OBLIGATORIO (bcrypt tiene $ literales)

# Brand-specific business config
# ... (per dominio brand)
EOF
```

**CRÍTICO:** documentar en comentario que valores con `$`/`!`/espacios requieren **single-quote** en `.env.dev` (caso paradigma: bcrypt hashes). Sin single-quote, bash interpreta `$2b` como variable expansion durante `source .env.dev` y rompe el hash silenciosamente (caso vitalia Bug #1 2026-05-18).

### Step 3 — Migration 001 snapshot (incluye tablas engine)

`{slug}/backend/alembic/versions/001_{slug}_initial_snapshot.py` DEBE crear las 3 tablas engine IAM:

```python
# {slug}/backend/alembic/versions/001_{slug}_initial_snapshot.py

def upgrade() -> None:
    # ENGINE IAM TABLES — matching luana_core_iam.{User,Tenant,UserTenant}Model
    # Copy schema verbatim desde nicolify/backend/alembic/versions/001_initial_snapshot.py:2210-2300
    # (proven canonical, no inventar variations brand)
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.tenants (
            id UUID PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(255) UNIQUE NOT NULL,
            config_json JSONB DEFAULT '{}'::jsonb,
            default_currency VARCHAR(3) DEFAULT 'USD',
            timezone VARCHAR(64) DEFAULT 'UTC',
            extraction_priority INTEGER DEFAULT 0,
            gemini_api_key VARCHAR(255),
            webhook_secret VARCHAR(255),
            can_use_platform_keys BOOLEAN DEFAULT FALSE,
            tracking_config JSONB DEFAULT '{}'::jsonb,
            weekly_start_day INTEGER DEFAULT 0,
            fiscal_year_start_month INTEGER DEFAULT 1,
            fiscal_year_start_day INTEGER DEFAULT 1,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.users (
            id UUID PRIMARY KEY,
            full_name VARCHAR(255),
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(50),
            clerk_id VARCHAR(255) UNIQUE,
            role VARCHAR(50) DEFAULT 'admin',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.user_tenants (
            user_id UUID NOT NULL REFERENCES users(id),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            role VARCHAR(50) DEFAULT 'admin',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (user_id, tenant_id)
        );
    """)

    # BRAND-SPECIFIC TABLES (después de las engine)
    # ... per vertical brand (clinics for vitalia, restaurants for lupulo, properties for guestly, etc.)
```

**Anti-pattern (LO QUE NO HAY QUE HACER):** crear tablas `{slug}_users`, `{slug}_tenants`, `{slug}_user_profiles` con SQL crudo asumiendo modelo distinto al engine. Esto fue el bug vitalia 2026-05-19 — admin code referenciaba `vitalia_clinics`/`vitalia_user_profiles`/`vitalia_tenants` que NO existían en ninguna migration.

### Step 4 — Backend consume engine (no SQL crudo)

`{slug}/backend/src/modules/{slug}/` debe consumir engine via Python imports:

```python
# {slug}/backend/src/modules/{slug}/admin/modules/users.py
from luana_core_iam.infrastructure.repositories import UserRepository, UserTenantRepository
from luana_core_iam.application.services import UserService
from luana_core_iam.infrastructure.models import UserModel, TenantModel, UserTenantModel

# NEVER:
# from sqlalchemy import text
# session.execute(text("SELECT * FROM {slug}_users WHERE ..."))   # ❌ phantom table
# session.execute(text("INSERT INTO {slug}_user_profiles ..."))   # ❌ reinvent engine

# ALWAYS:
def list_users_by_tenant(session, tenant_id):
    repo = UserRepository(session)
    return repo.list_by_tenant(tenant_id)   # ✅ engine service

def create_user_and_link_tenant(session, email, tenant_id, role):
    user_service = UserService(session)
    user = user_service.create_user(email=email)
    link_repo = UserTenantRepository(session)
    link_repo.link(user_id=user.id, tenant_id=tenant_id, role=role)
    return user
```

### Step 5 — Brand-extension tables ONLY for genuinely-brand-specific concepts

Vitalia tiene `clinic` (médico) brand-extension. Lupulo eventualmente tendrá `restaurant_location`. Guestly tendrá `property`. Fitflow tendrá `gym_location`. Cada uno con FK a `tenants.id` engine.

**Cuándo crear brand-extension table:**
- Concepto que el engine NO tiene
- Genuinamente único a la vertical (no replica concepto cross-brand existente)
- Tiene FK a `tenants.id` (mantiene relación engine ↔ brand)
- Documentado en `{slug}/docs/architecture/` ADR brand-local

**Cuándo NO crear brand-extension table (=mirror engine):**
- Reimplementar tabla `tenants` con prefix `{slug}_tenants`
- Reimplementar tabla `users` con prefix `{slug}_users`
- Reimplementar pattern que ya está en engine (extension SDK EP-1..EP-18 cubre overrides)

### Step 6 — Admin Streamlit puerto dedicado

Cada brand tiene admin Streamlit en puerto único:

| Brand | Backend | Frontend | Admin | DB | Redis |
|---|---|---|---|---|---|
| nicolify | 8001 | 3001 | 8501 | nicolify_dev | 0 |
| vitalia | 8002 | 3002 | 8502 | vitalia_dev | 1 |
| comunify | 8003 | 3003 | 8503 | comunify_dev | 2 |
| lupulo | 8004 | 3004 | 8504 | lupulo_dev | 3 |
| **saasora** | **8005** | **3005** | **8505** | **saasora_dev** | **4** |
| **inmoflow** | **8006** | **3006** | **8506** | **inmoflow_dev** | **5** |
| **retailly** | **8007** | **3007** | **8507** | **retailly_dev** | **6** |
| **fixia** | **8008** | **3008** | **8508** | **fixia_dev** | **7** |
| **guestly** | **8009** | **3009** | **8509** | **guestly_dev** | **8** |
| **fitflow** | **8010** | **3010** | **8510** | **fitflow_dev** | **9** |

Update `{slug}/docker-compose.dev.yml` con service `{slug}-admin`:

```yaml
{slug}-admin:
  build: ./backend
  container_name: luana-dev-{slug}_admin-1
  command: streamlit run src/modules/{slug}/admin/app.py --server.port=8501 --server.address=0.0.0.0
  ports:
    - "127.0.0.1:85{XX}:8501"
  environment:
    DATABASE_URL: ${DATABASE_URL}
    {SLUG}_ADMIN_PASSWORD_HASH: ${ {SLUG}_ADMIN_PASSWORD_HASH}
    # ... all other env vars same as backend
  depends_on:
    - luana_postgres_dev
```

Admin auth: bcrypt single super-admin password `{SLUG}_ADMIN_PASSWORD_HASH` env var (NO Clerk, admin no es customer-facing).

### Step 7 — Brand overlay rules

`{slug}/.claude/rules/{topic}.md` para reglas brand-specific (overlay, extiende `.claude/rules/` raíz). Mínimo: si compliance_level != standard, agregar rule `{compliance}-lite.md` (ver `vitalia/.claude/rules/hipaa-lite.md` como modelo).

### Step 8 — Capabilities + outcomes esqueleto

`{slug}/docs/product/capabilities/{module}/{capability}.yaml` — vacío al inicio, se pueblan al cerrar stories (R32 inventory enforcement).

`{slug}/docs/product/outcomes/{outcome-id}.md` — primer outcome típicamente "MVP launch" o "core IAM adoption".

`{slug}/docs/product/checkpoint.md` + `BACKLOG.md` — auto-gen via scripts pre-commit.

---

## Anti-patterns observados (catalogados con caso origen)

### AP1 — Reinventar tablas IAM por brand (caso vitalia 2026-05-19)

**Síntoma:** brand admin code hace SQL crudo a tablas `{slug}_users` / `{slug}_tenants` / `{slug}_user_profiles` que no existen en migrations.

**Causa raíz:** brand bootstrap olvidó (a) auditar engine, (b) consumir `luana-core-iam`, (c) ejecutar migrations 001 con CREATE TABLE engine.

**Fix:** outcome `admin-iam-adoption-platform.md` (2026-05-19) — vitalia adopta engine + reescribe admin + agrega CREATE TABLE engine en migration 001.

**Prevención futura:** Step 3+4 obligatorios en bootstrap pattern. Auditor /architect en ready package debe verificar brand consume engine antes de aprobar.

### AP2 — Hardcodes brand-specific en engine config (caso core/config.py 2026-05-19)

**Síntoma:** `core/luana-core-platform/core/config.py` tiene defaults `FRONTEND_URL = "https://app.nicolify.com"`, `QDRANT_COLLECTION = "visionarias_knowledge"`, etc. Brand consumer hereda silencioso.

**Causa raíz:** carve-out 2026-05-15 movió config.py al engine pero NO purgó los defaults brand-specific (herencia pre-multibrand).

**Fix:** promotion proposal `2026-05-19-purge-nicolify-defaults-core-config.md` — defaults vacíos + fail-fast si brand olvida override.

**Prevención futura:** template `{slug}/.env.dev.template` incluye bloque "brand-specific config" desde día 1. Engine no asume brand, brand debe explicitar.

### AP3 — Crear sub-unit organizational table en engine sin promotion proposal

**Síntoma:** brand A introduce concepto `sub-unit` (clinic, location, property, area, warehouse) y lo crea directamente en engine porque "es generalizable".

**Causa raíz:** violación principio brand-first, core-second.

**Fix preventivo:** brand A crea tabla `{slug}_sub_units` brand-local con FK `tenants.id`. Si brand B replica → promotion proposal EP-19 `TenantSubUnit` con lift formal.

### AP4 — Cerrar story state=done sin ejercitar admin smoke (caso vitalia 2026-05-18)

**Síntoma:** story `vitalia-auth-base-functional` cerró APPROVED + merged a main. Smoke admin Streamlit post-merge reveló 4 bugs no detectados.

**Causa raíz:** validators 04-validators.yaml no incluían admin path (cubrían FE auth + dashboard + middleware, no admin).

**Fix preventivo:** si story include admin scaffold, validators DEBEN incluir admin login + CRUD básico end-to-end. Gherkin scenarios mapear a tests admin reales.

### AP5 — Cross-brand mirror admin module

**Síntoma futuro hipotético:** vitalia + lupulo + saasora copian `nicolify/backend/.../admin/` con renames mecánicos.

**Prevención:** cuando 2da brand requiera admin similar → promotion proposal lift `luana-core-admin` con extension SDK EP-N para pages brand-specific. Engine define scaffold base, brand registra pages via extensions.py.

### AP6 — Valores con caracteres especiales sin single-quote en .env (caso vitalia Bug #1 2026-05-18)

**Síntoma:** bcrypt hash `$2b$12$...` cargado como `b2.i` (4 chars en vez de 60). Auth admin falla con `Invalid salt`.

**Causa raíz:** `set -a; . .env.dev; set +a` con valor sin quote → bash expande `$2b` y `$12` como variables.

**Fix:** documentar en `{slug}/.env.dev.template` que valores con `$`/`!`/espacios requieren single-quote.

### AP7 — Migrations no aplicadas post-bootstrap (caso vitalia 2026-05-19)

**Síntoma:** DB vitalia_dev en revision `001_vitalia`, 20 migrations pendientes. Admin queries fallaron porque columnas/tablas no existían.

**Causa raíz:** bootstrap creó migrations pero nadie corrió `alembic upgrade head` post-merge.

**Fix preventivo:** brand bootstrap pattern Step 9 (mandatory): `docker exec luana-dev-{slug}_backend_dev-1 alembic upgrade head` + verify `alembic current` = head_revision_id. Documentar en `{slug}/README.md` quickstart.

---

## Checklist /pm-luana bootstrap brand nueva

Cuando Chris dice "bootstrap brand {slug}", verificar:

- [ ] Step 0: auditoría cross-engine ejecutada + reporte qué cubre engine vs qué falta brand
- [ ] Step 1: scaffold desde `_pm-sistema-template/` ejecutado
- [ ] Step 2: brand.yaml + .env.dev.template completos con bloque "brand-specific config" canónico
- [ ] Step 3: migration 001 crea tablas engine (users, tenants, user_tenants) verbatim desde nicolify proven canonical
- [ ] Step 4: backend imports `luana_core_iam` (no SQL crudo)
- [ ] Step 5: brand-extension tables ONLY for conceptos no-engine, con FK tenants.id
- [ ] Step 6: admin Streamlit puerto dedicado + service en docker-compose + bcrypt password env var
- [ ] Step 7: brand overlay rules (compliance.md si != standard)
- [ ] Step 8: capabilities/outcomes esqueleto + checkpoint.md + BACKLOG.md
- [ ] Step 9: `alembic upgrade head` ejecutado + verify
- [ ] Step 10: smoke admin login + tenant listing + user listing end-to-end PASS antes de ratificar bootstrap done
- [ ] Step 11: INFRA-MATRIX regenerada via `make infra-matrix` (incluye puertos backend/frontend/admin/db/redis)
- [ ] Step 12: portfolio regenerada via `make portfolio` (PORTFOLIO.md auto-gen)
- [ ] Step 13: PR brand bootstrap a main con squash-merge + handoff a `/pm-{slug}` para primer outcome MVP

---

## Trazabilidad

- Outcome origen: `docs/product/outcomes/admin-iam-adoption-platform.md` (2026-05-19)
- Promotion proposal: `docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-defaults-core-config.md`
- Caso origen vitalia bug: `vitalia/docs/product/stories/vitalia-auth-base-functional/HANDOFF-next-session.md`
- Architecture base: `docs/architecture/luana-platform/01-core-audit.md` + `02-core-purge-audit.md` + ADR-001
- Engine reference: `core/luana-core-iam/` (44 .py + 14 tests, canonical IAM)
- Nicolify reference: `nicolify/backend/alembic/versions/001_initial_snapshot.py:2210-2300` (canonical CREATE TABLE engine pattern)
- Vitalia reference (post fix): `vitalia/backend/alembic/versions/001_vitalia_initial_snapshot.py` (después de adopt-luana-core-iam story)
- Anti-duplication rule: `.claude/rules/anti-duplication.md` § lift shared rule
- Bootstrap template: `.claude/skills/_pm-sistema-template/`
- INFRA-MATRIX: `docs/portfolio/INFRA-MATRIX.md` (puertos cross-brand)

## Bitácora

- 2026-05-19: file creado tras directiva Chris "agrega aprendizaje al skill pm-luana para no cometer el mismo error con las otras marcas". Origen: vitalia-auth-base-functional smoke reveló 4 bugs + auditoría engine reveló vitalia reinventó IAM en lugar de consumir luana-core-iam (existe + completo) + hardcodes Nicolify en core/config.py (cross-brand contamination).
