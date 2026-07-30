---
story_id: vitalia-crm-phi-base-tables-migration
brand: vitalia
type: service-story
arch_version: 1
schema_version: v4.1
architecture_pattern: ADR-vitalia-004
adr_004_compliance: n/a-with-rationale   # BE migración pura, sin sub-tab UI (ADR-004 cubre sub-tabs UI; esta es migración + repo wiring)
adr_007_ref: ADR-vitalia-007-phi-pgcrypto-encryption
last_modified: 2026-05-30
---

# 03-arch — Migración tablas PHI base (vitalia_patients full schema cifrado + vitalia_leads) + repo decrypt wiring

## 0. Context Summary

- **Story:** `vitalia-crm-phi-base-tables-migration` · service-story · module `crm` · release F2.
- **Architect run on:** 2026-05-30.
- **Objetivo:** crear `vitalia_leads` (net-new) + reconcile `vitalia_patients` (agregar columnas PHI faltantes), **cifradas at-rest con pgcrypto**, + cablear repos para descifrar/cifrar con KEK. Cierra el gap audit-on-patient-live de Slice 2.
- **Modules touched:** `vitalia/backend/src/modules/vitalia/crm/` (repos) + `_shared/encryption/` (consumo KEKClient) + `alembic/versions/` (035) + `scripts/` (seed) + env/compose (VITALIA_PHI_KEK).
- **Surface → builder → auditor mapping:**

  | Surface | Builder | Auditor |
  |---|---|---|
  | `alembic/versions/035_*.py` (migración pgcrypto) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
  | `crm/infrastructure/persistence/{patient,lead}_repository.py` (decrypt wiring) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
  | `crm/api/router.py` (KEK inject en DI) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
  | `scripts/seed_test_users_link.py` (paciente seed cifrado) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
  | `tests/{migrations,integration}/` | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |

  **NO FE. NO AGENTIC.** Cero tickets tocan `core/luana-core-*/src/` o `{copilot,sales_agent}/`.

- **Skills consulted:** `backend-expert` (Inside-Out DDD, SQLA 2.0, idempotent migration, response_model gate), `hipaa-lite.md` overlay (dual filter, pgcrypto BYTEA, audit sync, KEK no-log), `backend-migrations.md` (forward-only idempotent), `tenant-isolation.md` (tenant_id en toda query incl get_by_id).
- **CONTEXT-BRIEF source:** none present (story pequeña) → self-ran greps (Path B) para Existing Systems Audit.
- **capability YAML affected (post-merge):** `vitalia/docs/product/capabilities/iam/iam-scaffold-slice-1.yaml` (cap_change_type `fix` — habilita endpoints PHI ya existentes; append `change_log` entry, sin scenarios nuevos). Verificar cap real al merge (checkpoint cita `iam-scaffold-slice-1` con nota "cap real se decide en refining"); si el dueño semántico es `crm.crm-consent-optout` (los repos lo citan en `# cap:`), `/pm-vitalia` ajusta el target en Fase F.3.
- **Architecture gates que deben seguir verdes:** `tests/architecture/test_phi_dual_filter.py`, `test_audit_log_sync_write.py`, `test_audit_log_row_per_phi_endpoint.py`, `test_response_model_required.py`, `test_pgcrypto_phi_columns.py` (EXTENDER: agregar `(vitalia_patients, name/dni/...)` + `(vitalia_leads, name/...)` a `PHI_BYTEA_COLUMNS`), `test_no_legacy_eventbus_mock_when_outbox_on.py` (N/A — no toca eventos).

## 1. Domain Entities (sin cambios)

Las entidades de dominio `Patient` (`crm/domain/patient.py`) y `Lead` (`crm/domain/lead.py`) **NO cambian** — el cifrado es 100% a nivel infraestructura (columna BYTEA + repo encrypt/decrypt). El dominio sigue viendo `name: str`, `date_of_birth: datetime | None`, etc. en plaintext. Esto es correcto: el cifrado es una preocupación de persistencia, no de dominio.

## 2. Schema canónico (DERIVADO de los repos — fuente de verdad)

> Derivado leyendo TODAS las queries de `patient_repository.py` (get_by_id, list_by_filter, update, opt_out, marketing_opt_in) + `lead_repository.py` (get_by_id, list_by_filter). Columnas confirmadas contra `Patient`/`Lead` dataclasses.

### 2.1 `vitalia_patients` (PHI — dual filter tenant+clinic)

| Columna | Tipo físico | Cifrada | Notas |
|---|---|---|---|
| `id` | UUID PK | NO | `gen_random_uuid()` default (016 ya lo creó) |
| `tenant_id` | UUID NOT NULL | NO | root isolation |
| `clinic_id` | UUID NOT NULL | NO | dual filter HIPAA-lite |
| `name` | **BYTEA** | **SÍ** | PHI — `pgp_sym_encrypt` |
| `date_of_birth` | **BYTEA** | **SÍ** | PHI — al descifrar se castea a timestamp en repo |
| `dni` | **BYTEA** | **SÍ** | PHI nat'l ID |
| `phone` | **BYTEA** | **SÍ** | PHI |
| `email` | **BYTEA** | **SÍ** | PHI |
| `address` | **BYTEA** | **SÍ** | PHI |
| `marketing_opt_out_at` | TIMESTAMPTZ NULL | NO | metadata (repo lo lee directo) |
| `marketing_opt_in` | BOOLEAN NOT NULL DEFAULT FALSE | NO | flag (016 lo creó) |
| `opt_out` | BOOLEAN NOT NULL DEFAULT FALSE | NO | flag (016) |
| `opt_out_reason` | TEXT NULL | NO | metadata admin (ADR-007 D3) |
| `opt_out_at` | TIMESTAMPTZ NULL | NO | metadata (016) |
| `deleted_at` | TIMESTAMPTZ NULL | NO | soft delete |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT NOW() | NO | (016) |
| `updated_at` | TIMESTAMPTZ NOT NULL DEFAULT NOW() | NO | (016) |

**016 ya creó:** `id, tenant_id, clinic_id, created_at, updated_at, deleted_at, marketing_opt_in, opt_out, opt_out_reason, opt_out_at` + índices `ix_vitalia_patients_tenant_clinic`, `ix_vitalia_patients_opt_out`, `ix_vitalia_patients_marketing_opt_in`. **035 AGREGA (vía `ADD COLUMN IF NOT EXISTS`):** `name, date_of_birth, dni, phone, email, address, marketing_opt_out_at` (todas BYTEA excepto `marketing_opt_out_at` TIMESTAMPTZ). No re-crea las de 016 (IF NOT EXISTS las saltea).

> ⚠️ Drift dev: la DB dev está stampeada a 034 pero `vitalia_patients` **no existe físicamente** (016 nunca aplicó su DDL). Por eso 035 abre con `CREATE TABLE IF NOT EXISTS vitalia_patients (...)` con el **esqueleto completo de 016** (mismas columnas) ANTES de los `ADD COLUMN IF NOT EXISTS`, para reconstruir desde cero en la DB driftada. En una DB limpia (futura), 016 crea el esqueleto y 035 solo agrega PHI — ambos paths convergen idempotentes.

### 2.2 `vitalia_leads` (NO PHI — single tenant filter)

| Columna | Tipo físico | Cifrada | Notas |
|---|---|---|---|
| `id` | UUID PK | NO | `gen_random_uuid()` |
| `tenant_id` | UUID NOT NULL | NO | root isolation (NO clinic_id — Lead no es PHI) |
| `name` | **BYTEA** | **SÍ** | PII contacto |
| `email` | **BYTEA** | **SÍ** | PII |
| `phone` | **BYTEA** | **SÍ** | PII |
| `source` | TEXT NULL | NO | "website"/"instagram"/etc — se filtra |
| `status` | TEXT NOT NULL DEFAULT 'new' | NO | se filtra/indexa |
| `notes` | **BYTEA** | **SÍ** | puede contener PII (ADR-007 D3) |
| `deleted_at` | TIMESTAMPTZ NULL | NO | soft delete |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT NOW() | NO | |
| `updated_at` | TIMESTAMPTZ NOT NULL DEFAULT NOW() | NO | |

**035 crea net-new** `vitalia_leads` con `CREATE TABLE IF NOT EXISTS`. PK `id`.

### 2.3 Índices (solo sobre columnas plaintext — ADR-007 D4)

```sql
-- patients (016 ya creó los 3 de tenant/clinic/opt_out/marketing — IF NOT EXISTS los saltea)
CREATE INDEX IF NOT EXISTS ix_vitalia_patients_tenant_clinic ON vitalia_patients (tenant_id, clinic_id);
-- leads (nuevos)
CREATE INDEX IF NOT EXISTS ix_vitalia_leads_tenant   ON vitalia_leads (tenant_id);
CREATE INDEX IF NOT EXISTS ix_vitalia_leads_tenant_status ON vitalia_leads (tenant_id, status) WHERE deleted_at IS NULL;
```

**Prohibido:** índice sobre `name/dni/email/phone/address/notes` (ciphertext). Lookup por columna cifrada = follow-up (blind index).

## 3. Migración `035_vitalia_crm_phi_base_tables.py` (forward-only idempotente)

- **revision:** `"035_vitalia"` · **down_revision:** `"034_vitalia"` · path `vitalia/backend/alembic/versions/035_vitalia_crm_phi_base_tables.py`.
- **upgrade():**
  1. `op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")` (idempotente — ya en 013/005/025).
  2. `CREATE TABLE IF NOT EXISTS vitalia_patients (...)` — esqueleto 016 (id/tenant/clinic/timestamps/deleted + flags marketing) para reconstruir DB driftada.
  3. `ADD COLUMN IF NOT EXISTS` PHI BYTEA: `name, date_of_birth, dni, phone, email, address` + `marketing_opt_out_at TIMESTAMPTZ`.
  4. `CREATE TABLE IF NOT EXISTS vitalia_leads (...)` (full schema, PHI/PII BYTEA).
  5. `CREATE INDEX IF NOT EXISTS` (patients tenant/clinic; leads tenant + tenant/status).
- **downgrade()** (ADR-007 D5): `DROP TABLE IF EXISTS vitalia_leads` + `ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS {name,date_of_birth,dni,phone,email,address,marketing_opt_out_at}`. **NO** drop `vitalia_patients` (016 la owna). **NO** drop extension pgcrypto.
- **Patrón:** raw SQL `op.execute(...)`, NUNCA `op.create_table()` / `sa.Enum()`. Reusa estilo de 016/013/025.

## 4. Repo decrypt/encrypt wiring (pgcrypto inline + KEK bound param)

> Patrón cementado en ADR-007 D1: SQL crudo (estilo actual de los repos) con `pgp_sym_decrypt(col, :kek)::text` al leer y `pgp_sym_encrypt(:val, :kek)` al escribir. KEK desde `KEKClient.get_key()` (EXTEND del sistema existente `_shared/encryption/kek_client.py`).

### 4.1 KEK injection (DI)

- `KEKClient` se construye en el router (donde ya se construyen `AuditLogRepository`/`PatientRepository`) y se pasa al repo: `PatientRepository(session=session, audit_repo=audit_repo, kek=KEKClient.from_env())`. Default param `kek: KEKClient | None = None` → si None, el repo hace `KEKClient.from_env()` (back-compat para tests).
- El repo llama `self._kek.get_key()` una vez por query y lo bindea como `:kek`. **NUNCA** loguear `:kek` (structlog jamás incluye el valor — el repo ya loguea solo ids).

### 4.2 Patient read (get_by_id / list_by_filter)

```sql
SELECT id, tenant_id, clinic_id,
       pgp_sym_decrypt(name, :kek)::text          AS name,
       pgp_sym_decrypt(date_of_birth, :kek)::text AS date_of_birth,   -- repo castea text → datetime
       pgp_sym_decrypt(dni, :kek)::text           AS dni,
       pgp_sym_decrypt(phone, :kek)::text         AS phone,
       pgp_sym_decrypt(email, :kek)::text         AS email,
       pgp_sym_decrypt(address, :kek)::text       AS address,
       marketing_opt_out_at,
       marketing_opt_in, opt_out, opt_out_reason, opt_out_at,
       deleted_at, created_at, updated_at
FROM vitalia_patients
WHERE tenant_id = :tenant_id AND clinic_id = :clinic_id AND id = :entity_id AND deleted_at IS NULL
```
- `date_of_birth`: `pgp_sym_decrypt(...)::text` devuelve el timestamp serializado; el repo lo parsea a `datetime` (o None si la columna es NULL — guard `pgp_sym_decrypt` sobre NULL devuelve NULL).
- NULL-safe: una columna BYTEA NULL → `pgp_sym_decrypt(NULL, :kek)` = NULL → el repo mapea a None (igual que hoy).

### 4.3 Patient write (update — SET dinámico de campos PHI)

El `update()` actual construye SET dinámico desde `updates` dict. Para campos PHI cifrados, el SET debe envolver el valor en `pgp_sym_encrypt`:
```python
PHI_ENC_COLS = {"name", "date_of_birth", "dni", "phone", "email", "address"}
set_parts = []
for k in updates:
    if k in PHI_ENC_COLS:
        set_parts.append(f"{k} = pgp_sym_encrypt(:{k}, :kek)")
    else:
        set_parts.append(f"{k} = :{k}")
# params incluye :kek + cada :{k}
```
- `opt_out()` / `marketing_opt_in()` no tocan PHI cifrado → solo agregar `:kek` no es necesario ahí (no leen/escriben PHI). Sin cambios funcionales salvo que sigan compilando.

### 4.4 Lead read/write

Análogo: `pgp_sym_decrypt(name/email/phone/notes, :kek)::text` al leer; `pgp_sym_encrypt(:val, :kek)` al escribir (el repo lead actual no tiene `create`/`update` con SQL — los agrega `lead_service`/router; el write de PHI cifrado se aplica donde se inserte/actualice `name/email/phone/notes`).

> **Nota de scope:** `lead_repository.py` actual solo tiene `get_by_id` + `list_by_filter` (read). El `create`/`update` de leads vive en `lead_service` vía el router (`POST/PATCH /leads`). El builder debe localizar dónde se INSERTA el lead (repo o service) y aplicar `pgp_sym_encrypt` ahí. Si el insert no existe como SQL crudo todavía, se agrega en el repo (método `create`/`update`) consistente con el patrón.

## 5. KEK env wiring (cierra gap dev)

- `vitalia/.env.dev.template`: agregar `VITALIA_PHI_KEK=<hex 64 chars dev-only>` con comentario `# DEV-ONLY · NO usar en prod · prod=KMS (ADR-vitalia-007)`. Generar con `python3 -c "import secrets; print(secrets.token_hex(32))"`.
- `vitalia/docker-compose.dev.yml`: passthrough `VITALIA_PHI_KEK=${VITALIA_PHI_KEK}` en el service backend env.
- `vitalia/.env.dev` (gitignored, local): el builder lo setea para la verificación live.

## 6. Seed (SC-1/SC-5 — paciente cifrado)

`scripts/seed_test_users_link.py` (psycopg2 sync) — agregar 1 paciente Sanaré escrito **con `pgp_sym_encrypt`** para que quede cifrado:
```sql
INSERT INTO vitalia_patients (id, tenant_id, clinic_id, name, date_of_birth, dni, phone, email, address,
                              marketing_opt_in, opt_out, created_at, updated_at)
VALUES (%(id)s, %(tenant)s, %(clinic)s,
        pgp_sym_encrypt(%(name)s, %(kek)s), pgp_sym_encrypt(%(dob)s, %(kek)s),
        pgp_sym_encrypt(%(dni)s, %(kek)s), pgp_sym_encrypt(%(phone)s, %(kek)s),
        pgp_sym_encrypt(%(email)s, %(kek)s), pgp_sym_encrypt(%(address)s, %(kek)s),
        false, false, NOW(), NOW())
ON CONFLICT (id) DO NOTHING
```
- `kek` desde `os.environ["VITALIA_PHI_KEK"]` (mismo que el backend). Fixture: tenant=Sanaré (`TENANT_SANARE`), clinic=`CLINIC_SANARE`, id determinístico (uuid5) para que SC-1 lo lea por id conocido. Datos LatAm realistas neutros (no Lorem).
- Seed corre vía psycopg2 directo (NO el async repo) → el INSERT con `pgp_sym_encrypt` es la vía coherente con el seed existente.

## 7. Existing systems audit (NO NEW LAYER rule)

### Source of evidence
- [x] Self-run greps (Path B — no CONTEXT-BRIEF presente).

### Audit cross-module ejecutado
```
grep -rln "class KEKClient|pgp_sym_encrypt|pgp_sym_decrypt|KEKClient" vitalia/backend/src core/luana-core-*/src
  → vitalia/backend/src/modules/vitalia/_shared/encryption/kek_client.py (KEKClient)
  → .../fidelizacion/.../nps_service.py · .../marketing/.../channel_sync_state_repository.py (consumers)
  → core/: 0 matches
grep cross-brand (nicolify/comunify/lupulo): 0 matches → sin mirror, sin lift /pm-luana
```

### Sistemas existentes encontrados
| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| KEKClient (env-based KEK) | `vitalia/backend/src/modules/vitalia/_shared/encryption/kek_client.py` | active | **EXTEND** — inyectar en patient/lead repos. NEW sería violación NO-NEW-LAYER. |
| pgcrypto pattern (CREATE EXTENSION + pgp_sym_*) | `alembic/versions/025_vitalia_pgcrypto_nps_comment.py` | active (pero trigger+GUC roto: KEK nunca inyectada) | **EXTEND el cifrado** (pgp_sym_* inline) · **NO adoptar trigger+GUC** (roto — ver ADR-007 D1). Gap 025 = follow-up. |
| Migración idempotente IF NOT EXISTS | `016/013/032` | active | **REUSE pattern** (backend-migrations.md). |
| Tabla vitalia_patients (esqueleto) | `016_vitalia` | applied (chain) | **RECONCILE** (ADD COLUMN), NO editar 016 (forward-only). 035 downgrade NO la dropea (ADR-007 D5). |
| PhiRepositoryBase + AuditLogRepository | `_shared/repositories/` | active | **REUSE** — patient repo ya hereda; cero cambios. |

### Conclusión
Cero capa nueva. Cero mirror cross-brand. Cero edit de engine. Story = EXTEND de sistemas vitalia existentes + migración brand-local.

## 8. Integration design (CONN)

### Reachability path (cómo se LLEGA a las tablas nuevas)
```
doctor (JWT real Clerk) en god-matrix
  → GET /api/v1/crm/patients/{id}  (router.py::get_patient — YA existe, hoy da 500)
  → PatientService.get_by_id (RBAC @require_phi_access — YA existe)
  → PatientRepository.get_by_id (pgp_sym_decrypt + dual filter — wiring nuevo)
  → tabla vitalia_patients (creada por 035) → 200 + data descifrada + audit row
marketing/recepcion → 403 (RBAC ya existente) ; cross-tenant → 404 ; forjado → 401
GET /api/v1/crm/leads → LeadService.list_for_inbox → LeadRepository → vitalia_leads (035) → 200
```

### Consumers (quién USA las tablas)
- `vitalia_patients`: `PatientRepository` (get_by_id/list/update/opt_out/marketing_opt_in) ← `PatientService`/`PatientConsentService` ← endpoints `/crm/patients/*` (YA cableados en router, hoy 500). Consumidor real existente.
- `vitalia_leads`: `LeadRepository` (get/list) + `LeadService` (create/update/list_for_inbox) ← endpoints `/crm/leads*` (YA cableados). Consumidor real existente.
- **No hay islas:** las tablas no son net-new sin consumidor — son la base física que los endpoints PHI ya cableados de Slice 2 estaban esperando (de ahí el 500). Esta story las materializa.

### Registration points (ya cableados — esta story NO crea endpoints nuevos)
- `crm/api/router.py` ya hace `router.include_router(consent_router)` + define todos los endpoints `/patients` `/leads` `/conversations`. El router crm ya está montado en el app (Slice 2). **Esta story NO toca registration** — solo materializa las tablas + el decrypt wiring del repo.

### Home (cap)
- `cap_target: iam-scaffold-slice-1` · `cap_change_type: fix` (habilita endpoints PHI existentes; no agrega scenarios nuevos al cap). Al merge, `/pm-vitalia` confirma si el dueño semántico correcto es `crm.crm-consent-optout` (citado en los `# cap:` headers de los repos) y ajusta.

## 9. Architecture Decisions (resumen — detalle en ADR-vitalia-007)

- **KEK source:** env `VITALIA_PHI_KEK` (dev) vía `KEKClient` existente; KMS slot prod (deferred). Agrega el env var al template+compose (cierra gap que dejó 025).
- **Cifrado inline pgp_sym_* con :kek bound param** (NO trigger+GUC de 025 — está roto en runtime).
- **Columnas cifradas:** patients `name/date_of_birth/dni/phone/email/address`; leads `name/email/phone/notes`. Claves/flags/timestamps plaintext.
- **NO índices sobre cifrado** (blind index = follow-up).
- **Downgrade 035:** dropea solo `vitalia_leads` + columnas PHI que agregó; NUNCA `vitalia_patients` (016 la owna) ni pgcrypto.
- **Greenfield:** sin data-migration (no hay prod ni plaintext existente).
- **adr_004_compliance: n/a-with-rationale** — ADR-004 es el patrón de sub-tabs UI (9 secciones FE/route group); esta es una migración + repo wiring puro sin UI, fuera del scope de ADR-004. ADR-007 es el ADR aplicable.

## 9.5 Tests audit (default flip)

- [x] **No aplica — CONTRACT no flipea defaults side-effect.** Esta story no flipea ningún feature flag (`USE_*_PATTERN_*`, etc.). No toca eventos/outbox/LLM routing. Es schema + decrypt wiring.

## 10. File structure

| Path | NEW/MOD | Surface |
|---|---|---|
| `vitalia/backend/alembic/versions/035_vitalia_crm_phi_base_tables.py` | NEW | migración |
| `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/patient_repository.py` | MOD | decrypt/encrypt wiring + KEK param |
| `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/lead_repository.py` | MOD | decrypt wiring + KEK param + (create/update si insert vive aquí) |
| `vitalia/backend/src/modules/vitalia/crm/api/router.py` | MOD | inyectar `KEKClient.from_env()` en repos |
| `vitalia/backend/scripts/seed_test_users_link.py` | MOD | + 1 paciente Sanaré cifrado |
| `vitalia/.env.dev.template` + `vitalia/docker-compose.dev.yml` | MOD | `VITALIA_PHI_KEK` |
| `vitalia/backend/tests/migrations/test_035_crm_phi_base_tables_idempotency.py` | NEW | idempotency |
| `vitalia/backend/tests/integration/test_crm_phi_real_tables.py` | NEW | integration (real tables) |
| `vitalia/backend/tests/architecture/test_pgcrypto_phi_columns.py` | MOD | extender PHI_BYTEA_COLUMNS con patients/leads |

## 11. Cross-cutting concerns

- **Tenant isolation:** toda query patient filtra `tenant_id + clinic_id` (incl get_by_id) — ya cumplido por PhiRepositoryBase; leads filtra `tenant_id`. Sin cambios (los repos ya lo hacen).
- **PHI / PII:** `response_model=` ya en todos los endpoints (router). `PatientResponse` solo expone allowlist (name/email/phone/marketing_opt_out_at — NO dni/dob/address). Verificar que el decrypt NO amplíe el payload expuesto.
- **KEK secrecy:** `:kek` NUNCA en logs/traces/transcript. structlog del repo solo loguea ids. Verificación live imprime solo status codes + logs `grep`-eados sanitizados.
- **Encryption at-rest:** pgcrypto BYTEA (hipaa-lite § Encryption at rest) ✓.
- **Audit log:** sync write pre-response (ya cumplido por PatientRepository+AuditLogRepository). Sin cambios.
- **Master data / timezone:** `date_of_birth` cifrado se almacena serializado; al descifrar el repo lo parsea a datetime UTC-aware. `created_at/updated_at` TIMESTAMPTZ plaintext (sin cambio).
- **Spanish neutro:** N/A (sin UI; mensajes de error del router ya neutros).
- **Native-first:** migración aplica vía `docker exec ... alembic upgrade head`; tests/lint native (`${WS}/.venv/bin/pytest`).

## 12. Architecture fitness impact

- `test_pgcrypto_phi_columns.py` — **EXTENDER** `PHI_BYTEA_COLUMNS` con `(vitalia_patients, name)`, `(...,date_of_birth)`, `(...,dni)`, `(...,phone)`, `(...,email)`, `(...,address)`, `(vitalia_leads, name)`, `(...,email)`, `(...,phone)`, `(...,notes)`. Gate verifica BYTEA en migración.
- `test_phi_dual_filter.py` / `test_audit_log_sync_write.py` / `test_response_model_required.py` / `test_audit_log_row_per_phi_endpoint.py` — deben seguir verdes (sin cambios de allowlist; allowlists shrink-only).

## 13. capability YAML + modules updates (post-merge)

- `vitalia/docs/product/capabilities/iam/iam-scaffold-slice-1.yaml` (o `crm/crm-consent-optout.yaml` si /pm ajusta el target): append `change_log` entry `type: fix` documentando "tablas PHI base materializadas + cifrado at-rest → endpoints /crm/patients /crm/leads operativos". `scenarios_added: []` (fix no agrega scenarios).
- `vitalia/docs/product/modules/crm.md`: el bloque auto-list se regenera vía `scripts/reconcile_capabilities.py --brand vitalia` (no editar a mano).

## 14. Test surfaces (TDD RED-first)

- **Migration (RED primero):** `test_035_crm_phi_base_tables_idempotency.py` — re-run upgrade = no-op; columnas existen; BYTEA type; downgrade no dropea vitalia_patients.
- **Repo unit (RED primero):** round-trip encrypt→DB→decrypt (write paciente con KEK → leer → plaintext correcto). NULL-safe (columna NULL → None).
- **Integration (RED primero, real DB):** `test_crm_phi_real_tables.py` — `test_doctor_reads_patient_200_audit`, `test_marketing_403`, `test_cross_tenant_404`, `test_cross_clinic_403`, `test_phi_encrypted_at_rest_decrypted_on_read`. NO monkeypatch del repo (ejerce tablas reales). Monkeypatch SOLO `verify_token_payload` (deterministic, per learning 2026-05-30).
- **Live (anti-teatro, supervisado):** re-god-matrix mint JWT real → /patients/{id} 200 + audit row + raw-DB ciphertext + /leads 200 + marketing 403 + cross-tenant 404. Logs leídos.

## 15. Research notes

- **pgcrypto `pgp_sym_encrypt/decrypt`** — verificado contra el patrón vitalia existente (`025_vitalia_pgcrypto_nps_comment.py`, accessed 2026-05-30). No requiere research externo (Postgres builtin, ya en uso en el repo). Opus 4.8 cutoff Jan 2026 — pgcrypto API es estable, sin cambios post-cutoff.
- **Clerk god-matrix mint** — `vitalia/docs/learnings/2026-05-30-clerk-godmatrix-mint-live-verification.md` (accessed 2026-05-30): 3-curl mint (POST /sessions → POST /sessions/{id}/tokens) para JWT real. NUNCA imprimir secret/JWT/PHI.
- **KEKClient** — `_shared/encryption/kek_client.py` (accessed 2026-05-30): env `VITALIA_PHI_KEK` hex ≥32 bytes, cache, `from_env()` factory. Slot KMS prod documentado en el docstring.

## 16. Open questions for PM

- **OQ-1b resuelto (ADR-007 D2):** KEK = env `VITALIA_PHI_KEK` dev vía KEKClient + KMS slot prod. ✓
- **OQ-2 (legacy tree):** las 5 migraciones en `src/modules/vitalia/persistence/migrations/` (020-023) NO las corre el alembic.ini activo (`script_location = alembic`). **Decisión arch:** documentar arqueológicas (sub-scope, NO limpiar inline). Follow-up: story dedicada para decidir limpieza/merge. Builder agrega un comentario en el `__init__.py` legacy señalando "tree huérfano — ver ADR-vitalia-007 follow-up".
- **OQ-3 resuelto:** seed extiende `seed_test_users_link.py` con 1 paciente Sanaré cifrado. ✓
- **OQ-4 resuelto:** greenfield, sin data-migration. ✓
- **Follow-ups registrados (NO esta story):** (1) trigger+GUC de 025 nunca inyecta KEK → wirear o deprecar; (2) blind index para lookup por dni/email cifrado; (3) adapter KMS prod + rotación anual; (4) limpieza legacy tree.
