# 07-merge — vitalia-crm-phi-base-tables-migration

> Brand: vitalia · Module: crm · Release: F2 · Merge by: /pm-vitalia · 2026-05-30
> Verdict auditor: APPROVED (CHECKPOINTS C1-C5 todos verdes) · cap_change_type: fix

## § 1 — Gherkin verification matrix

(copia de `06-audit/gherkin-matrix.md` · 5/5 PASS)

| Scenario | Ticket | Evidencia | Status |
|---|---|---|---|
| SC-1 doctor → GET /patients/{id} 200 + audit row | T-2/T-3 | LIVE: 200 + name descifrado (len 20) + audit `read_patient` 0→1; integration test_doctor_reads_patient_200_audit | ✅ |
| SC-2 marketing → 403 | T-3 | LIVE: marketing JWT real → 403; test_marketing_403 | ✅ |
| SC-3 migración idempotente | T-1 | test_035_crm_phi_base_tables_idempotency.py GREEN; LIVE: alembic upgrade head re-run no-op (head 035) | ✅ |
| SC-4 cross-tenant 404 / forjado 401 | T-3 | LIVE: cross-tenant 403 (role-reject, no leak) / not-found 404 (dual-filter) / forjado 401 | ✅ |
| SC-5 PHI cifrado at-rest | T-2/T-3 | LIVE: raw name=88 octets magic byte 0xc3 (PGP ciphertext); API descifra para rol autorizado; test_phi_repo_encrypt_decrypt.py GREEN | ✅ |

## § 2 — Playwright E2E / verificación live

- Service-story BE → **no aplica Playwright** (sin UI nueva).
- En su lugar: **verificación live god-matrix anti-teatro** con JWT real de Clerk + conteos DB reales. Evidencia completa: `VERIFICATION-godmatrix-live.md`.
- Resultado: doctor 200 + descifrado + audit persiste · marketing 403 · cross-tenant 404 · forjado 401 · at-rest ciphertext (0xc3) · logs limpios (sin 500/column/KEK).

## § 3 — Capabilities updated/created

- `vitalia/docs/product/capabilities/iam/iam-scaffold-slice-1.yaml` — **append `change_log` entry `type: fix`** (cap_change_type=fix, sin scenarios nuevos). Documenta: tablas PHI base materializadas + cifrado pgcrypto at-rest + fix commit unit-of-work → endpoints CRM PHI operativos end-to-end con audit persistiendo. Cierra el gap audit-on-patient-read del Slice 2 (SC-1 antes verificado contra /crm/conversations stub; ahora sobre /crm/patients/{id} real).
- `crm/crm-consent-optout.yaml` — NO tocado (deprecated/superseded por vitalia-fase2-valeria-pacientes).
- No se crean caps nuevos (fix).

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/crm.md` + `modules/iam.md` — bloque auto-list se regenera vía `scripts/reconcile_capabilities.py --brand vitalia` (post-merge, no editar a mano · R3).

## § 5 — How to verify (reproducible)

```bash
WS=$(git rev-parse --show-toplevel)
# 1. Migración aplicada
docker exec luana-dev-vitalia_backend_dev-1 bash -lc "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic current"   # → 035_vitalia (head)
# 2. Tablas + columnas PHI BYTEA
docker exec luana-dev-luana_postgres_dev-1 psql -U postgres -d vitalia_dev -tA -c \
  "SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_name IN ('vitalia_patients','vitalia_leads') AND column_name IN ('name','dni','email','notes') ORDER BY 1,2"   # → bytea
# 3. Tests (nativo)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest \
  tests/architecture/test_pgcrypto_phi_columns.py \
  tests/migrations/test_035_crm_phi_base_tables_idempotency.py \
  tests/modules/vitalia/crm/test_phi_repo_encrypt_decrypt.py \
  tests/unit/test_db_committing_session.py -q
# 4. At-rest ciphertext (raw, no KEK → ilegible)
docker exec luana-dev-luana_postgres_dev-1 psql -U postgres -d vitalia_dev -tA -c \
  "SELECT octet_length(name), to_hex(get_byte(name,0)) FROM vitalia_patients LIMIT 1"   # → 88, c3 (paquete PGP)
# 5. Live god-matrix (JWT real) — ver VERIFICATION-godmatrix-live.md § matriz
```

## Commits

| | SHA | Contenido |
|---|---|---|
| T-1 | 540249cb | migración 035 pgcrypto BYTEA (reconcile patients + leads net-new) + arch test + idempotency |
| T-2 | e67c67a1 | repos decrypt/encrypt + KEK bound param + LeadRepository.create/update + router DI + env |
| T-3 | 3ee9aed9 | seed cifrado + integration tests reales |
| fix | 62b068ac | commit unit-of-work gap (audit rows + writes) — descubierto por verificación live |
| audit | 9706b9ca | CHECKPOINTS + Phase D + T-audit-review |

## Follow-ups registrados (NO esta story)

1. **Cross-cutting (escalado):** 18 módulos usan `get_async_session` sin commit explícito en API → posible gap unit-of-work en otros módulos que escriben. Story de plataforma dedicada (auditar commit de cada endpoint que escribe, o promover `get_async_session_committing` como default con migración controlada).
2. W-1: `tests/modules/vitalia/crm/api/conftest.py` patchea el `get_async_session` ahora no usado por crm (dead patch) → actualizar a `get_async_session_committing` o eliminar.
3. ADR-007 follow-ups: trigger+GUC 025 roto (KEK nunca inyectada), blind index para lookup por dni/email cifrado, adapter KMS prod + rotación anual, legacy tree (5 migraciones huérfanas en src/).
4. W-2: SC-4 cross-clinic devuelve 404 (dual-filter) en vez de 403 (resolver role-level) — sin leak, comportamiento pre-existente Slice 2; alinear semántica si se desea 403 explícito.

## Learning candidates (cross-brand → ping /pm-luana)

- **Content-Type fix en god-matrix mint:** el endpoint Clerk `/v1/sessions/{id}/tokens` ahora exige `Content-Type: application/json` (el learning 2026-05-30 lo omitía). Actualizar `vitalia/docs/learnings/2026-05-30-clerk-godmatrix-mint-live-verification.md`.
- **`get_async_session_committing` (unit-of-work pattern):** candidato de lift cross-brand (toda brand con endpoints que escriben + audit sync necesita esto).
- **Lección anti-teatro:** HTTP 201/200 + structlog "written" NO prueban persistencia — confirmar con conteo DB. El fix commit-gap fue invisible a tests mockeados, visible solo en god-matrix live.
