# T-2 Implementation Log — BE repos-wire (cablear repos PHI reales + async_resolve migration)

story: vitalia-iam-slice2-phi-real-auth
ticket: T-2
builder: builder-backend (Sonnet 4.6)
date: 2026-05-29
state: IN_PROGRESS

---

## Skills Consulted (must_load enforcement)

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Runtime-quality-checklist, Inside-Out DDD, repo wiring patterns | Use `PatientRepository(session, AuditLogRepository(session))` for PHI; `LeadRepository(session)` for non-PHI; no AsyncMock in runtime paths |
| `tessl__fastapi` | Annotated deps, Depends(get_async_session), async endpoint migration | Add `session: Annotated[AsyncSession, Depends(get_async_session)]` to every PHI endpoint in crm/consent; migrate `_resolve_context` to async |
| `tessl__pytest-api-testing` | Integration test extension, monkeypatch, DB fixtures | APPEND to existing test_phi_real_auth.py (SC-2/SC-3 tests) — remove skip, assert real effect |
| `.claude/rules/tenant-isolation.md` | Every query filters tenant_id + clinic_id (PHI repos) | Confirm repos pass both; lead repos pass tenant_id only (non-PHI, per arch) |
| `.claude/rules/backend-ddd.md` | Inside-Out layering, no cross-module imports | Repos injected via session in factory; no imports from other modules |
| `.claude/rules/tdd-mandatory.md` | RED tests before GREEN code | First entry = RED test for SC-2 + SC-3 written before implementation |
| `.claude/rules/test-design-doctrine.md` | Verification REAL ≠ HTTP 200 | SC-2 → assert HTTP 403 status + assert PHI NOT in response body. SC-3 → assert 404 / 403 + body no-leak. |
| `vitalia/.claude/rules/hipaa-lite.md` | Dual filter tenant+clinic, audit log row, role enforcement | async_resolve resolves role from DB; role checked per endpoint; audit_log row written via PatientRepository methods |

---

## Sub-scope (OQ-1) — endpoint → repo real

| Endpoint | Repo real | Status |
|---|---|---|
| GET /patients/{id} | `PatientRepository(session, AuditLogRepository(session))` | EXISTS — real repo ships |
| PATCH /patients/{id} | `PatientRepository(session, AuditLogRepository(session))` | EXISTS — real repo ships |
| POST /patients/{id}/opt-out | `PatientRepository(session, AuditLogRepository(session))` | EXISTS — real repo ships |
| PATCH /patients/{id}/marketing-opt-in | `PatientRepository(session, AuditLogRepository(session))` | EXISTS — real repo ships |
| GET /leads/{id} | `LeadRepository(session)` | EXISTS — real repo ships |
| GET /leads | `LeadRepository(session)` | EXISTS — real repo ships |
| POST /leads | `LeadRepository(session)` | EXISTS — real repo ships |
| PATCH /leads/{id} | `LeadRepository(session)` | EXISTS — real repo ships |
| GET /conversations | `resolver.async_resolve` (role check only; no conv repo needed for 403 gate) | ROLE GATE ONLY — returns empty list via Slice 1 stub (no ConversationRepository wired yet per scope) |
| GET /conversations/{id} | `resolver.async_resolve` (role check only; 404 always in Slice 1) | ROLE GATE ONLY |
| marketing routes | `resolver.async_resolve` (role from DB) | Existing real service repos already wired |
| inbox routes | `resolver.async_resolve` (role from DB) | Existing real service repos already wired |

**Note on ConversationRepository in crm/router.py**: The two conversation endpoints (list/detail) only perform role-check and return empty list / 404. They do NOT instantiate ConversationRepository internally. Therefore they don't have an AsyncMock to remove — they just need `async_resolve` migration for the auth path. This is within scope.

**Note on crm/router.py Lead endpoints**: Lead is non-PHI. Real `LeadRepository(session)` wired. For `create_lead` and `update_lead`, the Slice 1 stub returns a stub Lead — with real repo wired: create_lead will call `lead_repo.create()` (real), update_lead will call the real repo. If `vitalia_leads` table doesn't exist in test DB, the integration test will fail at DB level — but the UNIT test (SC-2/SC-3) tests role gating, not DB persistence.

---

## Plan (technical design)

### Strategy

T-2 is primarily a **migration** ticket:
1. Replace `resolver.resolve(token)` with `await resolver.async_resolve(token, session, x_tenant_id, x_clinic_id)` in all 5 files.
2. Remove `from unittest.mock import AsyncMock` inline blocks from runtime paths in `crm/router.py` and `crm/consent_endpoints.py`.
3. Wire real repos: `PatientRepository(session, AuditLogRepository(session))` + `LeadRepository(session)`.
4. Add `session: Annotated[AsyncSession, Depends(get_async_session)]` as endpoint param where missing.

### Role enforcement for 403 (SC-2)

After `async_resolve`, `ctx.role` is the DB-sourced role (not token). The existing `_PHI_ROLES` check in crm/router.py and `PHIAccessDeniedError` logic in service calls naturally enforce role. For role `recepcion` or `marketing` (not in PHI roles) → `PHIAccessDeniedError` is raised → HTTP 403. The audit denial row is written via the service's audit call (which calls `PatientRepository.opt_out` / service method that calls audit_repo.write). For the role-check-only conversation endpoints and for `_resolve_context` (pre-service), we raise HTTPException(403) directly after checking ctx.role — no separate audit row in those fast-exit paths (the service audit would handle it if the service were reached).

**SC-2 test strategy**: Mock `async_resolve` to return ClinicContext with `role="recepcion"` and expect HTTP 403. No DB needed.

**SC-3 test strategy**: Mock `async_resolve` to return ClinicContext with `role="doctor"` but with a *different* tenant_id or clinic_id. For cross-tenant: the repo's dual-filter query returns None → 404. For cross-clinic (same tenant, wrong clinic_id): repo returns None → 404 (or service raises PHIAccessDeniedError → 403). Test asserts body does NOT contain PHI names/emails.

### ANTI-ISLA check
- `PatientRepository` is CONSUMED by PatientService, PatientConsentService → both called by endpoints ✅
- `LeadRepository` is CONSUMED by LeadService → called by endpoints ✅
- `async_resolve` returns ClinicContext → consumed by role checks in all 5 router files ✅

---

## Iteration Log

### [RED] 2026-05-29 — SC-2 + SC-3 tests written before implementation

Writing RED tests first:
1. `test_recepcion_403()` — SC-2: role=recepcion → HTTP 403 from GET /patients/{id}
2. `test_marketing_403()` — SC-2: role=marketing → HTTP 403 from PATCH /patients/{id}/marketing-opt-in
3. `test_cross_tenant_404()` — SC-3: role=doctor but tenant_id mismatch → 404 + no PHI leak
4. `test_cross_clinic_403()` — SC-3: role=doctor but clinic_id mismatch → 403 + no PHI leak

These tests are RED before the router migration (still uses sync `resolve()` which returns stub empty role → different behavior than async_resolve with real role).

### [GREEN] 2026-05-29 — Implementation

Migration files:
1. `vitalia/backend/src/modules/vitalia/crm/api/router.py` — async_resolve + real repos
2. `vitalia/backend/src/modules/vitalia/crm/api/consent_endpoints.py` — async_resolve + real repos
3. `vitalia/backend/src/modules/vitalia/marketing/api/deps.py` — async_resolve
4. `vitalia/backend/src/modules/vitalia/marketing/api/routes.py` — async_resolve
5. `vitalia/backend/src/modules/vitalia/inbox/api/router.py` — async_resolve

Test file:
6. `vitalia/backend/tests/integration/test_phi_real_auth.py` — EXTEND (SC-2 + SC-3 tests)

---

## Gate Results

(populated after pytest run)

---

## AsyncMock grep expectation

After implementation, `grep -n "AsyncMock" vitalia/backend/src/modules/vitalia/crm/api/` must return ZERO results.
`grep -n "AsyncMock" vitalia/backend/src/modules/vitalia/marketing/api/` must return ZERO results.
`grep -n "AsyncMock" vitalia/backend/src/modules/vitalia/inbox/api/` must return ZERO results.

---

## Gate Results (finalized by orchestrator — builder stalled mid-debug, work sound in tree)

- Integration `test_phi_real_auth.py` (SC-1..SC-4) + inbox routers: **49 passed** deterministic + 7 random seeds (111/222/333/444/555/777/999) → 49 passed cada uno. **NO flakiness** (la preocupación del builder de random-ordering era paranoia; los inbox tests ya migrados al nuevo wiring async_resolve).
- Arch fitness: **324 passed** (incluye test_phi_dual_filter, test_audit_log_sync_write, test_audit_log_row_per_phi_endpoint, test_response_model_required, test_no_phi_in_url_params, test_auth_stub_env_gate).
- ruff check src/modules/vitalia/{iam,crm,marketing,inbox}/ → All checks passed. ruff format → 8 files already formatted.

## Sub-scope (OQ-1) — endpoint → repo real (confirmado)

Repos PHI reales cableados via `Depends(get_async_session)` (cero inventado):

| Módulo | Repos reales instanciados |
|---|---|
| crm/api/router.py | PatientRepository, LeadRepository |
| crm/api/consent_endpoints.py | PatientRepository (consent) |
| inbox/api/router.py | MessageRepository, ConversationRepository, ActionReceiptRepository, ActivityEventRepository, LeadRepository |
| marketing/api/routes.py + deps.py | LucasRecommendationRepository, ChannelMetricRepository, AttributionMatrixSnapshotRepository, ReferralsLeaderboardSnapshotRepository (+ rol desde DB via async_resolve) |

**Nota AsyncMock residual (NO regresión T-2):** `inbox/api/router.py:130-142` tiene un `_AsyncMock()` PRE-EXISTENTE (en HEAD pre-T-2, no tocado por T-2) que es el **fallback offline del outbox event bus** (`luana_core_events.outbox.adapter_bus`), import-guarded (`except ImportError`). NO es un repo PHI ni el path de auth/resolve. En runtime real (engine importable) usa el `adapter_bus` real. Queda como sub-scope honesto (limpieza del fallback offline del bus = follow-up, fuera del mandato T-2 de repos PHI).

## CONN (anti-isla) verificado

- **Consumed:** async_resolve cableado real — crm/router(4) + consent(2) + marketing/deps(4) + inbox(2). Repos reales consumidos por sus endpoints.
- **Notarized:** routers ya montados en main.py (sin ruta nueva); wiring DI interno.
- **Navigable:** FE manda JWT real + X-Tenant-ID + X-Clinic-ID → endpoints PHI alcanzables con rol-desde-DB.
