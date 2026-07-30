# T-2 Result — pgcrypto KEK wiring (repos + router + env)

**Story:** vitalia-crm-phi-base-tables-migration  
**Ticket:** T-2  
**Commit:** e67c67a1  
**Branch:** wip/vitalia  
**Status:** TESTS-PASSING (awaiting gate-runner + auditor-backend)

---

## Files modified (8)

| File | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/patient_repository.py` | MOD — pgp_sym_decrypt reads, pgp_sym_encrypt update, kek param, _parse_dob |
| `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/lead_repository.py` | MOD — pgp_sym_decrypt reads, pgp_sym_encrypt write, kek param, create()+update() added |
| `vitalia/backend/src/modules/vitalia/crm/api/router.py` | MOD — KEKClient imported + injected in all 6 repo construction sites |
| `vitalia/backend/src/modules/vitalia/crm/api/consent_endpoints.py` | MOD — KEKClient imported + injected in 2 PatientRepository sites |
| `vitalia/.env.dev.template` | MOD — VITALIA_PHI_KEK placeholder added (DEV-ONLY comment) |
| `vitalia/docker-compose.dev.yml` | MOD — VITALIA_PHI_KEK env passthrough for backend service |
| `vitalia/backend/tests/modules/vitalia/crm/test_phi_repo_encrypt_decrypt.py` | NEW — 20 RED→GREEN tests |
| `vitalia/backend/tests/modules/vitalia/crm/api/conftest.py` | NEW — autouse KEK+session stubs for CRM API unit tests |

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Inside-Out DDD, SQLA 2.0 raw SQL patterns, TDD flow | Applied: raw SQL text() with bound params; no ORM import in domain; no business logic in API layer |
| `tessl__fastapi` | Annotated deps, response_model gate, DI injection | Applied: KEKClient.from_env() injected inline at repo construction (consistent with existing pattern, no major DI refactor) |
| `tessl__pytest-api-testing` | httpx AsyncClient, fixture scoping, DB isolation | Applied: autouse conftest with KEK+session stubs; test_phi_repo_encrypt_decrypt.py uses AsyncMock session |
| `.claude/rules/tenant-isolation.md` | Verify every query filters tenant_id (incl get_by_id) | Verified: patients dual filter (tenant_id+clinic_id), leads single filter (tenant_id) — both in all SELECT/UPDATE/INSERT |
| `.claude/rules/backend-ddd.md` | Domain no-change, repo is infra layer, KEK is infra concern | Applied: crm/domain/ untouched; KEK wiring 100% in infrastructure layer |
| `vitalia/.claude/rules/hipaa-lite.md` | PHI dual filter, KEK secrecy, encrypt at-rest | Applied: _PHI_ENC_COLS frozenset, pgp_sym_encrypt/decrypt pattern, AV-kek-not-logged verified clean |

---

## Implementation Plan (from technical_design phase)

### Domain (no changes)
- `crm/domain/patient.py` + `crm/domain/lead.py` — untouched. Encryption is 100% infrastructure concern.

### Infrastructure (primary T-2 work)
- `PatientRepository`: `kek: KEKClient | None = None` param; `from_env()` back-compat if None. `get_by_id` + `list_by_filter` wrap PHI cols in `pgp_sym_decrypt(col, :kek)::text AS col`. `update()` builds dynamic SET: PHI cols get `pgp_sym_encrypt(:val, :kek)`, non-PHI direct. `_parse_dob()` helper at module level for text→datetime (None-safe).
- `LeadRepository`: same KEK pattern. Adds `create()` (INSERT with pgp_sym_encrypt for name/email/phone/notes) and `update()` (dynamic SET) — these were called by `lead_service` but did not exist.

### API (KEK injection)
- `router.py`: `from src.modules.vitalia._shared.encryption.kek_client import KEKClient`. All 4 `LeadRepository(session=session)` → `LeadRepository(session=session, kek=KEKClient.from_env())`. Both `PatientRepository(session=session, audit_repo=audit_repo)` → `PatientRepository(..., kek=KEKClient.from_env())`.
- `consent_endpoints.py`: same injection for 2 PatientRepository sites.

### Env
- `.env.dev.template`: `VITALIA_PHI_KEK=REPLACE_ME_run_python3_secrets_token_hex_32` with comment.
- `docker-compose.dev.yml`: `VITALIA_PHI_KEK: "${VITALIA_PHI_KEK}"` passthrough.

---

## Tests (RED → GREEN)

### New tests (test_phi_repo_encrypt_decrypt.py — 20 tests)
All 20 pass. Tests cover:
- `TestPatientRepositoryKEKParam` (3): kek=None→from_env, kek=injected, back-compat no-arg
- `TestPatientRepositoryEncryptDecryptSQL` (4): get_by_id has pgp_sym_decrypt+:kek, list_by_filter has pgp_sym_decrypt+:kek, update has pgp_sym_encrypt+PHI_ENC_COLS, _parse_dob helper exists
- `TestPatientRepositoryNullSafe` (1): BYTEA NULL → date_of_birth=None
- `TestLeadRepositoryKEKParam` (3): same pattern
- `TestLeadRepositoryEncryptDecryptSQL` (5): get_by_id, list_by_filter, create exists+async, create has pgp_sym_encrypt, update exists+async, update has pgp_sym_encrypt
- `TestLeadRepositoryNullSafe` (1): email NULL → None
- `TestRouterKEKInjection` (2): router.py imports KEKClient, consent_endpoints.py imports KEKClient

### Regression check
- Pre-T-2: `test_crm_api.py`, `test_consent_endpoints.py`, `test_router_conversation_detail.py`, `test_router_conversations_list.py` — **already failing before T-2** (verified via `git stash` comparison). These are pre-existing issues (missing env vars for full app startup + broken async mock patterns). T-2 did NOT introduce these failures.
- All other CRM tests (208): pass
- Architecture tests (330): pass

---

## Quality Gates Output

```
ruff check vitalia/backend/src/modules/vitalia/crm/ ... → All checks passed!
ruff format --check ... → 36 files already formatted
pytest tests/modules/vitalia/crm/ (excl. pre-existing failures) → 208 passed
pytest tests/architecture/ → 330 passed, 2 warnings
AV-kek-not-logged: grep -rnE 'logger.*kek|log.*get_key|print.*kek' → OK KEK no logueada
AV-no-engine-edit: git diff --name-only | grep core/luana-core- → OK no engine edits
AV-no-cross-brand: git diff --name-only | grep nicolify/comunify/lupulo/ → OK no cross-brand
```

Note: `F-repo-roundtrip` (round-trip encrypt→DB→decrypt) requires a live Postgres DB with pgcrypto. These tests are covered in T-3 integration tests (`test_crm_phi_real_tables.py`). The unit tests in T-2 verify SQL structure and NULL-safety via mock sessions (consistent with the T-1 pattern).

---

## ADR-007 compliance

- **D1**: Inline `pgp_sym_*` with `:kek` bound param. NO trigger+GUC (025 pattern remains deprecated per ADR-007).
- **D2**: KEK from `VITALIA_PHI_KEK` env via `KEKClient.from_env()`.
- **D3**: PHI cols encrypted: patients `{name,date_of_birth,dni,phone,email,address}`; leads `{name,email,phone,notes}`.
- **D4**: No index on encrypted columns (verified: only plaintext cols indexed).
- **D5**: N/A for T-2 (downgrade handled in T-1 migration).

---

## Pre-existing test failures (documented — not T-2 regressions)

| File | Pre-T-2 state | Root cause |
|---|---|---|
| `test_crm_api.py` | FAILED | Imports `from src.main import app` which requires full env vars (missing in test env) |
| `api/test_consent_endpoints.py` | FAILED | Same — imports real app |
| `api/test_router_conversation_detail.py` | FAILED | MagicMock not awaitable in async path |
| `api/test_router_conversations_list.py` | FAILED | Same |

These were failing in the T-1 baseline (`git stash` + run confirms). T-2 work scope ends here.
