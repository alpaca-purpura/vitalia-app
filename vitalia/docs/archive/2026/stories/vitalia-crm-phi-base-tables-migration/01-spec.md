---
story_id: vitalia-crm-phi-base-tables-migration
brand: vitalia
type: service-story
state: refining
po_version: 2
cap_target: iam-scaffold-slice-1
cap_change_type: fix
ratified_by_chris: true   # v2 2026-05-30: Chris ratificó incluir pgcrypto (PHI encryption at-rest)
architecture_pattern: ADR-vitalia-004
adr_004_compliance: n/a-with-rationale   # BE migración pura, sin sub-tab UI
last_modified: 2026-05-30
hotfix_metadata:
  repro_verified: true
  repro_command: "JWT real Clerk → GET http://127.0.0.1:8002/api/v1/crm/leads → HTTP 500; docker logs luana-dev-vitalia_backend_dev-1 → 'relation \"vitalia_leads\" does not exist'"
  diagnosis_validates_handoff: true
  diagnosis_correction: "Profundización: vitalia_patients tampoco existe (drift stamp-vs-apply) Y su schema canónico (PHI columns name/dni/dob/phone/email/address) excede lo que 016 crea — 016 solo el esqueleto + columnas marketing."
---

# 01-spec — Migración tablas PHI base: crear vitalia_leads + reconcile vitalia_patients (full schema)

## Context

**Origen:** la verificación live god-matrix de `vitalia-iam-slice2-phi-real-auth` (done 2026-05-30) expuso vía anti-teatro que con JWT real los endpoints PHI de paciente/lead dan **HTTP 500** — las tablas base no existen en dev. Esto bloqueó el cierre live del grader audit-on-patient de SC-1 de aquella story.

**Repro (verificado live):** doctor JWT real → `GET /api/v1/crm/leads` → 500 (`relation "vitalia_leads" does not exist`). `GET /api/v1/crm/patients/{id}` → 500 (misma causa, `vitalia_patients` ausente).

**Causa raíz (2 problemas):**
1. **Drift stamp-vs-apply:** `vitalia_dev` en `alembic_version=034` (head) pero `vitalia_patients` no existe. `016` la crea con `CREATE TABLE IF NOT EXISTS` pero la DB fue stampeada sin aplicar el DDL → `alembic upgrade head` NO la recrea (el guard la considera aplicada).
2. **Migración faltante + schema incompleto:**
   - `vitalia_leads` no se crea en ningún árbol de migración.
   - `vitalia_patients`: incluso `016` solo crea el esqueleto (`id, tenant_id, clinic_id, created_at, updated_at, deleted_at` + marketing). Pero `patient_repository.py` SELECTea columnas PHI **que 016 no crea**: `name, date_of_birth, dni, phone, email, address, marketing_opt_out_at`. El schema canónico vino de "Story 11" (árbol legacy `src/modules/vitalia/persistence/migrations/`, no corrido por el alembic.ini activo).

## Objetivo

Migración forward-only idempotente (`035`) que **reconcile el schema canónico completo** de `vitalia_patients` (incluyendo PHI columns que el repo lee) + **crea `vitalia_leads`** (schema del repo), con índices dual-filter, sin romper la cadena 034→035 ni editar migraciones aplicadas. Verificación anti-teatro: re-god-matrix con JWT real → endpoints PHI 200 + audit row.

## Prior art applied (anti-duplication-refining)

- **REUSE pattern idempotente** `CREATE TABLE IF NOT EXISTS` + `ALTER ... ADD COLUMN IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS` de `002/003/004/016` (backend-migrations.md). NO inventar pattern.
- **Schema canónico = fuente de verdad los repos** (`patient_repository.py` + `lead_repository.py` SELECT/UPDATE columns). El architect deriva el DDL exacto leyendo TODAS las queries de esos repos (no solo get_by_id).
- **NO engine:** tablas PHI brand-local (SQL crudo en repos vitalia). Cero consumo `luana-core-crm` para el schema.
- **Forward-only:** NO editar `016` (aplicada en la cadena). Nueva `035`.

## Schema esperado (borrador — architect deriva exacto de los repos)

> **★ v2 — pgcrypto in scope (ratificado Chris 2026-05-30):** las columnas PHI identitarias se almacenan **cifradas at-rest** vía `pgcrypto` (`pgp_sym_encrypt`/`pgp_sym_decrypt`, symmetric KEK). Greenfield: las tablas NO existen en dev y NO hay prod (deploy diferido) → se crean cifradas desde el inicio, **sin migración de datos plaintext existentes**. La migración corre `CREATE EXTENSION IF NOT EXISTS pgcrypto`.

- **vitalia_patients**: `id, tenant_id, clinic_id` (claves, NO cifradas — se filtran), **PHI cifrado** `name, date_of_birth, dni, phone, email, address` (columnas `BYTEA`, `pgp_sym_encrypt` al escribir), `marketing_opt_in, opt_out, opt_out_reason, opt_out_at, marketing_opt_out_at` (flags/metadata, NO PHI sensible — plaintext OK), `deleted_at, created_at, updated_at`. PK `id`. Índices: `(tenant_id, clinic_id)` + opt_out/marketing partial. **NO indexar columnas cifradas** (búsqueda por dni/email cifrado = fuera de scope; si se necesita lookup → blind index = follow-up).
- **vitalia_leads**: `id, tenant_id` (claves), **PHI/PII cifrado** `name, email, phone` (BYTEA), `source, status, notes` (notes puede contener PII → architect decide cifrar; default cifrar notes), `deleted_at, created_at, updated_at`. PK `id`. Índice `(tenant_id)` + `(tenant_id, status)`. Lead solo tenant_id (no dual-clinic per lead_repository — architect confirma).

### Surface ampliada por pgcrypto (v2)

El cifrado at-rest expande los archivos in-scope más allá de la migración:
- **Repos** `patient_repository.py` + `lead_repository.py`: `SELECT pgp_sym_decrypt(name, :kek)::text AS name, ...` al leer + `pgp_sym_encrypt(:name, :kek)` al escribir. Hoy leen plaintext → deben descifrar.
- **Key management (KEK):** la KEK simétrica viene de config (env `VITALIA_PHI_KEK` o KMS — architect decide, hipaa-lite.md pide "KEK rotada anualmente, backups con key separada"). NUNCA hardcodear la key. NUNCA loguear la key.
- **Sanitization/traces:** el PHI descifrado NUNCA va a logs/traces sin `sanitize_payload` (hipaa-lite).

## Definición de DONE

1. Migración `035_vitalia_crm_phi_base_tables.py` idempotente (`CREATE EXTENSION IF NOT EXISTS pgcrypto` + `CREATE TABLE IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`): crea `vitalia_patients` (full schema, **PHI columns cifradas BYTEA**) + `vitalia_leads` (PHI/PII cifrado) + índices (NO sobre columnas cifradas). down_revision `034_vitalia`.
2. `alembic upgrade head` en dev → ambas tablas existen con todas las columnas que los repos leen (cero column-not-exist al ejercerlas).
3. **Repos descifran (pgcrypto):** `patient_repository.py` + `lead_repository.py` leen con `pgp_sym_decrypt` y escriben con `pgp_sym_encrypt` usando la KEK de config. La API devuelve plaintext al rol autorizado; la DB almacena ciphertext.
4. **Verificación live (anti-teatro, OBLIGATORIA):** JWT real doctor → `GET /crm/patients/{id}` **200 + data descifrada + audit row** en `vitalia_audit_log` + `GET /crm/leads` **200**. recepcion/marketing → **403**. cross-tenant → **404** (no leak). Logs backend leídos (sin 500/column-error, sin la KEK ni PHI plaintext en logs). Cierra el grader audit-on-patient-live de la story previa.
5. **Encryption at-rest verificada:** query SQL crudo a `vitalia_patients` muestra **ciphertext (bytea)** en las columnas PHI, NO plaintext. La API descifra solo para el rol autorizado.
6. Tests: migration idempotency (re-run = no-op) + integration que ejerza /patients y /leads contra DB real (no monkeypatch del repo) + round-trip encrypt→DB→decrypt.
7. (Sub-scope documentado) decisión sobre las 5 migraciones legacy en `src/modules/vitalia/persistence/migrations/`: documentar como arqueológicas o flag follow-up (NO limpiar inline salvo trivial).

## Scenarios (5 · happy + negative + edge + adversarial + security · graders ejecutables)

### SC-1 · happy — doctor con JWT real lee paciente (200 + audit row)
- **given:** migración 035 aplicada en dev; doctor.demo con JWT real + X-Tenant-ID Sanaré + X-Clinic-ID; un paciente seed en `vitalia_patients` para ese tenant+clinic.
- **when:** `GET /api/v1/crm/patients/{id}`.
- **then:** 200 + data del paciente (dual filter tenant+clinic) + **audit_log row** escrito sync en `vitalia_audit_log` (action `phi_access_granted`, user, timestamp). Sin column-error.
- **graders:**
  - `{ type: integration, path: "vitalia/backend/tests/integration/test_crm_phi_real_tables.py::test_doctor_reads_patient_200_audit" }`
  - `{ type: state_check, target: db, query: "SELECT 1 FROM vitalia_audit_log WHERE action LIKE 'phi_access_granted%' ORDER BY occurred_at DESC LIMIT 1" }`
  - `{ type: manual_audit, who: claude-dev-app, expect: "JWT real → GET /crm/patients/{id} 200 + audit row + log sin 500/column-error" }`

### SC-2 · negative — rol no-PHI (recepcion/marketing) → 403
- **given:** marketing.demo (o recepcion) con JWT real válido; paciente existe.
- **when:** `GET /api/v1/crm/patients/{id}`.
- **then:** 403 (`@require_phi_access`) + audit log del intento denegado + sin leak de PHI en body.
- **graders:**
  - `{ type: integration, path: ".../test_crm_phi_real_tables.py::test_marketing_403" }`
  - `{ type: manual_audit, expect: "marketing JWT real → 403 + audit denied" }`

### SC-3 · edge — migración idempotente (re-run = no-op)
- **given:** migración 035 ya aplicada (tablas existen con datos).
- **when:** re-ejecutar la migración (upgrade/downgrade/upgrade o re-run del DDL).
- **then:** no-op sin error, sin pérdida de datos, sin DROP de columnas existentes (IF NOT EXISTS / ADD COLUMN IF NOT EXISTS lo garantizan).
- **graders:** `{ type: contract_test, path: "vitalia/backend/tests/migrations/test_035_crm_phi_base_tables_idempotency.py" }`

### SC-5 · security — PHI cifrado at-rest (pgcrypto round-trip)
- **given:** migración 035 aplicada (pgcrypto + columnas BYTEA); un paciente escrito vía el repo (write con `pgp_sym_encrypt`).
- **when:** (a) query SQL crudo `SELECT name FROM vitalia_patients` (sin descifrar); (b) `GET /crm/patients/{id}` con doctor JWT real.
- **then:** (a) la columna `name` devuelve **ciphertext/bytea** (NO el nombre plaintext) → cifrado at-rest confirmado; (b) la API devuelve el nombre **descifrado** (plaintext) al rol autorizado. La KEK nunca aparece en logs.
- **graders:**
  - `{ type: integration, path: ".../test_crm_phi_real_tables.py::test_phi_encrypted_at_rest_decrypted_on_read" }`
  - `{ type: state_check, target: db, query: "SELECT name FROM vitalia_patients LIMIT 1  -- debe ser bytea ciphertext, no plaintext" }`
  - `{ type: manual_audit, expect: "raw DB = ciphertext ; API read = plaintext ; KEK no en logs" }`

### SC-4 · adversarial — cross-tenant / cross-clinic / JWT inválido sobre tablas ahora vivas
- **given:** doctor JWT real (o token inválido).
- **when:** `GET /crm/patients/{id}` con X-Tenant-ID de otro tenant (cross-tenant), o X-Clinic-ID de otra clínica (cross-clinic), o token forjado.
- **then:** cross-tenant → 404 (no leak, dual filter); cross-clinic → 403; token forjado → 401. Audit del intento. (La auth de Slice 2 sigue intacta sobre los endpoints ahora funcionales.)
- **graders:**
  - `{ type: integration, path: ".../test_crm_phi_real_tables.py::test_cross_tenant_404" }`
  - `{ type: integration, path: ".../test_crm_phi_real_tables.py::test_cross_clinic_403" }`
  - `{ type: manual_audit, expect: "cross-tenant → 404 sin leak; forjado → 401" }`

## Acceptance gates (resumen)

```bash
WS=$(git rev-parse --show-toplevel)
# Migración + idempotency:
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/migrations/test_035_crm_phi_base_tables_idempotency.py tests/integration/test_crm_phi_real_tables.py -v
# Aplicar en dev + verificar tablas:
docker exec luana-dev-vitalia_backend_dev-1 bash -lc "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic upgrade head"
# Verificación live (anti-teatro): JWT real → /crm/patients/{id} 200 + audit row ; /crm/leads 200 ; recepcion 403
```

## Open questions (para architect / Chris)

- **OQ-1 (schema canónico + columnas a cifrar):** el architect deriva el DDL exacto de `vitalia_patients` leyendo TODAS las queries de `patient_repository.py` (SELECT + UPDATE) + `lead_repository.py`. Confirma qué columnas cifrar: identitarias PHI (`name, date_of_birth, dni, phone, email, address`) cifradas; claves (`tenant_id, clinic_id, id`) y flags (`marketing_opt_in, opt_out*`) NO. Leads: `name, email, phone, notes` cifrado.
- **OQ-1b (KEK source) ★ pgcrypto ratificado:** ¿de dónde sale la KEK simétrica? Propuesta: env `VITALIA_PHI_KEK` (dev) con doc de rotación anual + key de backup separada (hipaa-lite.md). ¿O preferís integrar un KMS/secret manager ya? (Default: env var dev + ADR documentando el path a KMS para prod. El architect lo cementa en 03-arch.)
- **OQ-2 (legacy tree):** 5 migraciones en `src/modules/vitalia/persistence/migrations/` no corridas por el alembic.ini activo. ¿Documentar arqueológicas (default) o limpiar en este story? (Default: documentar, limpieza = follow-up.)
- **OQ-3 (seed paciente):** SC-1/SC-5 necesitan un paciente seed (escrito vía el repo para que se cifre). ¿Extender `seed_test_users_link.py` con 1 paciente Sanaré (default) o seed dedicado?
- **OQ-4 (prod data):** N/A confirmado — no hay prod (deploy diferido) ni datos plaintext existentes en dev → greenfield, se crea cifrado desde el inicio. Si en el futuro prod tuviera filas plaintext (Story 11), la migración de cifrado de datos existentes sería una story aparte (NO esta).

## Próximo paso

Spec ratificada → `/architect` produce ready package (03-arch deriva schema canónico exacto de los repos + 04-validators + 05-guidelines + 06-tickets). Build SUPERVISADO (autonomous_mode false: migración + verificación live).
