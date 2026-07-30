# VERIFICATION — god-matrix live (anti-teatro)

**Story:** vitalia-crm-phi-base-tables-migration · **Fecha:** 2026-05-30 · **Modo:** autónomo supervisado (orchestrator ejecuta + reporta evidencia)
**Regla aplicada:** `verification-real-not-200` + `test-design-doctrine.md § Verificación REAL ≠ "HTTP 200"` + `hipaa-lite.md`
**Disciplina:** nunca se imprimieron CLERK_SECRET_KEY / KEK / JWT / PHI plaintext. Solo status codes + conteos DB + bytes/octetos.

## Setup (dev real)

- Migración `035_vitalia` aplicada en dev: `alembic current` = **035_vitalia (head)**. `034 → 035` ejecutada contra `vitalia_dev`.
- `VITALIA_PHI_KEK` (hex 64, dev-only) seteada en `.env.dev` + passthrough compose → backend recreado, KEK presente en container (len=64, valor nunca impreso).
- Seed: 1 paciente Sanaré + 1 lead, INSERT con `pgp_sym_encrypt`. IDs determinísticos:
  - `PATIENT_SANARE_DEMO = 87fee4d3-2742-5221-be1c-ec40a67fe3b9`
  - tenant Sanaré `e69a691d-070e-5caf-a053-6e74642ec100` · clinic `f035be5b-0ac4-5210-8fc3-395650ca2b83`
- JWT real Clerk minteado vía Backend API (god-matrix pattern, learning 2026-05-30). ⚠️ El endpoint `/v1/sessions/{id}/tokens` ahora exige `Content-Type: application/json` (el snippet del learning lo omitía → fix aplicado).

## Schema en DB real (post-035)

```
information_schema.tables → vitalia_patients, vitalia_leads  (ambas existen físicamente)
vitalia_patients PHI cols = bytea: name, date_of_birth, dni, phone, email, address ; marketing_opt_out_at = timestamptz
vitalia_leads    PHI cols = bytea: name, email, phone, notes ; source, status = text
```

## Matriz de escenarios (JWT real, no monkeypatch)

| # | Escenario | Resultado live | Esperado | Veredicto |
|---|---|---|---|---|
| SC-1 | doctor → `GET /api/v1/crm/patients/{id}` | **200** · `name` descifrado (len=20) · fields = `clinic_id,created_at,email,id,marketing_opt_out_at,name,phone,tenant_id` | 200 + data descifrada + PII allowlist | ✅ |
| SC-1 | audit row persiste | `vitalia_audit_log.action='read_patient'` rows **0 → 1 → 3** (sube por request) | row escrito + commiteado | ✅ |
| SC-1b | doctor → `GET /api/v1/crm/leads` | **200** | 200 | ✅ |
| SC-2 | marketing → `GET /patients/{id}` | **403** | 403 RBAC | ✅ |
| SC-3 | migración idempotente | `test_035_crm_phi_base_tables_idempotency.py` + re-run `alembic upgrade head` = no-op | re-run no-op | ✅ |
| SC-4a | doctor cross-tenant (X-Tenant-ID inexistente) | **403** (resolver de rol rechaza antes del query — sin leak) | no leak | ✅ |
| SC-4b | doctor ctx válido + patient inexistente | **404** (dual-filter `tenant_id+clinic_id` no encuentra → no leak) | 404 | ✅ |
| SC-4c | token forjado | **401** (decoder JWKS rechaza) | 401 | ✅ |
| SC-5 | PHI cifrado at-rest | raw `SELECT name` → `convert_from(...,'UTF8')` falla con `0xc3 0x0d`; octet_length=88; magic byte **0xc3** (paquete PGP) | ciphertext, NO plaintext | ✅ |
| SC-5 | API descifra para rol autorizado | SC-1 devuelve `name` legible (len 20) | round-trip | ✅ |

**PII allowlist (HIPAA-lite):** la respuesta de `/patients/{id}` expone solo `name/email/phone/marketing_opt_out_at` (+ ids/timestamps). **NO** expone `dni`, `date_of_birth`, `address` (cifrados, fuera del `response_model`). ✅

**Logs durante la matriz:** sin `500 internal`, sin `column/relation does not exist`, sin leak de `VITALIA_PHI_KEK`. Los únicos tracebacks son del decoder JWT rechazando el token forjado (SC-4c → 401, comportamiento esperado).

## Matiz registrado (no-blocker)

- **SC-4 cross-clinic** (tenant válido, clinic ajena) devuelve **404** (el dual-filter `tenant+clinic` excluye la fila) en lugar de **403**. No hay leak (404 no revela existencia, es incluso más conservador). El RBAC clinic-level (403 en el resolver antes del query) es comportamiento **pre-existente de Slice 2** — esta story no tocó el resolver. Documentado para el auditor; no bloquea SC-4 (la propiedad de seguridad — cero leak cross-clinic — se cumple).

## Bug encontrado y corregido por el anti-teatro (★)

La verificación live destapó un **bug pre-existente (Slice 2)** invisible bajo tests mockeados: los endpoints CRM usaban `get_async_session` (que **nunca commitea**) y tampoco committeaban explícito → los audit rows PHI y los writes (`POST /leads` → **HTTP 201 sin row en DB**) se flusheaban y **rollbackeaban** al cerrar la sesión.

- **Síntoma teatro:** `POST /leads` → 201, `phi_audit_log_written` en structlog → todo "verde", pero `SELECT count(*)` en DB = sin cambio.
- **Causa raíz:** unit-of-work sin dueño (`get_async_session` delega commit al caller; ningún caller crm committeaba).
- **Fix (commit `62b068ac`, scoped a `crm/api`):** dependency aditivo `get_async_session_committing` (commit on clean return / rollback + re-raise on error). NO modifica `get_async_session` (cero impacto en los otros 17 módulos).
- **Re-verificado LIVE (conteos DB):** `GET /patients` → audit `read_patient` **0→1** · `POST /leads` → `vitalia_leads` **1→2**. Regresión: `tests/unit/test_db_committing_session.py`.

## Finding cross-cutting (escalado, NO resuelto acá)

18 módulos consumen `get_async_session`; ninguno committea en su capa API. Algunos persisten vía commits explícitos en sus repos (`clinics_repository`, `audit_writer`), pero **otros módulos que escriben podrían tener el mismo gap** (audit rows / writes perdidos silenciosamente). Es **stake-asimétrico + cross-cutting** (blast radius 18 módulos) → **no se toca en esta story**. Recomendación: story de plataforma dedicada que audite el unit-of-work de cada endpoint que escribe (o promueva `get_async_session_committing` como default con migración controlada).

## Commits de la story

| Ticket | Commit | Contenido |
|---|---|---|
| T-1 | `540249cb` | migración 035 (pgcrypto BYTEA, reconcile patients + leads net-new) + arch test extendido + idempotency test |
| T-2 | `e67c67a1` | repos decrypt/encrypt + KEK bound param + LeadRepository.create/update + router DI + env |
| T-3 | `3ee9aed9` | seed paciente/lead cifrado + integration tests reales (skip-clean sin DB) |
| fix | `62b068ac` | commit unit-of-work gap (audit rows + writes) — descubierto por la verificación live |
