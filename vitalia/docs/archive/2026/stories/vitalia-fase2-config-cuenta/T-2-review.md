<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Backend Code Review: T-2 · Cuenta del tenant (config.cuenta) — clinics account fields + fiscal/specialty validators + account_router

**Date:** 2026-06-12
**Brand:** vitalia
**Story / PR:** vitalia-fase2-config-cuenta · T-2 (BE) · commits `ce34c4b0` + `120f5390` + `0350bd73` (BE-side)
**Files Reviewed:** 13 BE product files + 6 BE test files + migration 039 + main.py wiring
**Domains touched:** clinics (EXTEND), _shared (NEW validation+catalogs), audit (CONSUME), brand_studio (downstream)
**Skills consulted:** backend-expert · brand-expert (specialties JSONB engine-boundary) · hipaa-lite overlay · anti-duplication (Cat 12 scan)
**Auditor live-verify:** YES — exercised real PATCH write + read DB effect + read logs (see § Live-verify by auditor)
**Verdict:** **CHANGES_REQUESTED**

> **Headline:** the implementation is clean, well-tested at unit level, tenant-isolated, and passes all 8 gates. BUT a **live-confirmed HIPAA-lite audit-durability defect** silently drops the audit-log row on every account PATCH (returns 200, business data persists, audit row is rolled back at session close). This breaks a brand-mandatory invariant (`hipaa-lite.md` § Audit log) on an endpoint that writes tenant fiscal/legal data. The `dod_evidence` claim of `audit_log_async_written ×2` is a **false-positive** (structlog line ≠ committed DB row — `verification-real-not-200`). This is the only blocker; everything else is PASS/info.

---

## /test-backend Gate Status (from gate-output.json — all PASS)

| # | Gate | Result | Detail |
|---|---|---|---|
| 1 | ruff (lint) | PASS | 0 errors |
| 2 | ruff (format) | PASS | 0 reformats |
| 3 | pytest (clinics) | PASS | 91 new-suite tests green |
| 4 | pytest (arch selective) | PASS | response_model · no-query-without-tenant · audit-sync-marker · migrations-idempotent |
| 5 | tsc | PASS | (FE — T-1 scope) |
| 6 | eslint | PASS | (FE) |
| 7 | vitest (features) | PASS | (FE) |
| 8 | vitest (arch) | PASS | (FE) |

`any_fail=false`. Pre-existing skip `test_pgcrypto_phi_columns.py` (treatment_plans / migration 005) is NOT this story — correctly excluded.

> ⚠️ **Gate gap (root cause of the defect below):** the `test_audit_log_sync_write.py` marker gate is a presence/static check; the new-suite `test_patch_account_writes_audit_log_sync` asserts only `mock_audit_writer.write.assert_called_once()` (mocked session). **No test exercises the real transaction lifecycle**, so the audit row never persisting was invisible to the green suite. This is exactly why the bug shipped.

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 |
| 2 | Tenant Isolation | PASS | 0 (live-confirmed: cross-tenant→404) |
| 3 | Soft Deletes | PASS | 0 |
| 4 | Code Quality | PASS | 0 (gates green) |
| 5 | SQLAlchemy 2.0 | PASS | 0 |
| 6 | Async Consistency | PASS | 0 |
| 7 | Pydantic v2 / PII | PASS | 0 (clinic identity non-PHI, justified) |
| 8 | Migration Quality | PASS | 0 |
| 9 | **Security (HIPAA-lite audit)** | **FAIL** | **1 — audit row not persisted (live-confirmed)** |
| 10 | Tests / TDD | WARN | 1 — no real-session test for audit durability |
| 11 | Cross-cutting | PASS | 0 |
| 12 | Mirror detection | PASS | 0 (no cross-brand mirror) |
| 13 | Connectivity (CONN) | PASS | 0 (notarized + reachable) |

## Cross-scope flags

| File | Module | Action |
|---|---|---|
| `core/@luana/ui-kit/src/organism/shell/{AppPanelSlot,ShellLayoutClient,types}.tsx` | design-system package (TS, shell organism) | **`[CROSS-SCOPE — FE/design-system]`** → `auditor-frontend` + (if API-surface) `/pm-luana` lift review. NOT a `core/luana-core-*/src/` engine edit; NOT backend. Out of THIS auditor's scope; NOT scored here. (Context: fix_session_2026-06-12 documents this as a backward-compat regression fix of the 3cb9d5a0 lift — optional prop, FE side.) |
| `vitalia/frontend/src/features/config/**` | FE T-1 | `auditor-frontend` |
| `vitalia/backend/src/modules/vitalia/crm/**` (in broad diff range only) | crm | NOT this story (commits 59894c99 / 732794a0) — excluded from scope |

No `core/luana-core-*/src/` engine edits. No cross-brand pollution. **0 auto-FAIL scope violations.**

---

## Findings

### FAIL — C9-1: Account PATCH silently drops the HIPAA-lite audit-log row (live-confirmed)
**Category:** 9 (Security / HIPAA-lite) · also touches Cat 1 atomicity
**Files:**
- `clinics/api/account_router.py:76-81` (`_get_db` uses non-committing `get_async_session`)
- `clinics/application/clinic_account_service.py:207-219` (audit `write()` after repo commits, no final commit)
- `clinics/infrastructure/repositories/clinic_repository.py:208` + `clinic_config_repository.py:86` (each repo commits its own write **before** the audit write)
- `audit/audit_writer.py:157-211` (`write()` executes the INSERT but does NOT commit — by design it relies on the unit-of-work owner to commit)

**Issue (root-caused + live-verified):**
The endpoint mounts on `get_async_session` (the *non-committing* dependency — `src/db.py:57`, "Caller is responsible for commit/rollback"). The flow in `patch_account` is:
1. `update_account()` → `db.execute(UPDATE clinic)` → `db.commit()` ✓ (clinic fields persist)
2. `update_specialties()` → `db.execute(UPDATE tenant)` → `db.commit()` ✓ (specialties persist)
3. `audit_writer.write()` → `db.execute(INSERT vitalia_audit_log …)` → **no commit**
4. handler returns → `get_async_session` closes the session **without committing** → the audit INSERT (a fresh transaction opened after step 2's commit) is **rolled back**.

The `structlog` line `audit_log_async_written` fires inside `write()` (so the builder "saw" it), but the row never commits. This is the *exact* bug the `get_async_session_committing` dependency was created to fix for the CRM surface (`src/db.py:73-95` docstring: "PHI audit rows … were flushed-then-rolled-back at session close (HTTP 200 with no DB row)") — now recurring on config-cuenta.

**Live evidence (auditor exercised the real write):**
- `PATCH /api/v1/clinics/account/` with `{"legal_name":"AUDITOR-PROBE LATAM S.A."}` (tenant `e69a691d-070e-…`, role `owner`) → **HTTP 200**, `legal_name` **persisted** in `vitalia_clinic_branches` ✓
- `SELECT COUNT(*) FROM vitalia_audit_log WHERE action='clinic_account_patch'` → **0** (before AND after the PATCH) ✗
- Sanity: 843 total audit rows exist; other surfaces persist fine (`brand_identity_updated`=290, `doctor.updated`=10). The bug is specific to this endpoint's transaction wiring.

**Why this is a FAIL (not WARN):** `vitalia/.claude/rules/hipaa-lite.md` § Audit log: "TODA lectura/modificación … registra row. NO opcional. NO async fire-forget (sync write antes response)." The endpoint modifies tenant fiscal/legal identity (`legal_name`, `fiscal_id`, `address`, …) with zero audit trail. Cat 9 FAIL → overall FAIL per verdict math. The `dod_evidence` (`audit_log_async_written ×2`) is a false-positive; the DoD live-verify floor is NOT actually met for the auditable-write requirement.

**Fix (precise — mirror an existing working pattern; pick ONE):**
- **Option A (preferred — also fixes atomicity C1-2):** switch `account_router._get_db` to `get_async_session_committing` (already used by `marca_router.py:56,145` for exactly this case) AND remove the intermediate `db.commit()` calls inside `ClinicRepository.update_account` and `ClinicConfigRepository.update_specialties`. Then clinic fields + specialties + audit row commit **atomically once** on clean return; any raise rolls back all three. This is the cleanest and restores the arch § 7 "same commit" atomicity guarantee.
- **Option B (minimal):** keep `get_async_session`, add `await self.db.commit()` in `patch_account` immediately after the `audit_writer.write(...)` call (mirrors `doctors_router.py:277` `# flush audit log entry`). Does NOT fix atomicity (clinic and specialties still commit separately upstream).

**Regression test required (TDD RED→GREEN — why this is CHANGES_REQUESTED not auditor self-fix):** add an **integration** test (real session, `@pytest.mark.integration`, NOT mocked repos) that PATCHes account and asserts `SELECT COUNT(*) FROM vitalia_audit_log WHERE action='clinic_account_patch' AND resource_id=<clinic_id>` ≥ 1 after the request completes. The current mocked test (`test_patch_account_writes_audit_log_sync`) only asserts the method was *called*, which is why this shipped green.

**Routing rationale (Auditor Responsable v5):** audit-log/HIPAA-lite compliance is a **stake-asymmetric** category (security/compliance). Per `.claude/rules/auditor-self-fix-policy.md` v5 decision tree, the auditor does NOT silently self-patch a compliance invariant — it returns CHANGES_REQUESTED with the fix + regression-test design (Carril C'). Builder (`/dev-team`) applies Option A + the integration test, re-runs gates, re-exercises live (PATCH → row present), then re-hands to auditor.

---

### WARN — C1-2: Atomicity diverges from arch § 7 "same commit" (clinic vs specialties)
**Category:** 1 (DDD / transaction boundary)
**File:** `clinic_account_service.py:191-204` + the two repos that each `commit()`.
**Issue:** 03-arch § 7 + § Architecture Decisions declared "clinic fields + config_json specialties en el MISMO commit (atomicidad — si una falla, ambas revierten)." In code, `update_account` commits, THEN `update_specialties` commits separately. If `update_specialties` raises after `update_account` committed, clinic fields persist while specialties don't (partial state). Low probability (validation runs pre-persist, line 188-189), non-PHI, but it IS a ratified-invariant divergence.
**Fix:** subsumed by C9-1 **Option A** (single unit-of-work). If the builder picks Option B for the audit fix, also remove the per-repo commits so the boundary is one commit. **Note for next story:** the repos owning their own `commit()` is the structural anti-pattern here — `update_account`/`update_specialties`/`soft_delete`/`create` all `commit()` internally, which prevents the service from composing an atomic unit-of-work. Consider migrating clinics repos to caller-owned commit (consistent with `get_async_session_committing`).

### WARN — C10-1: No real-session test for audit/transaction durability (gate blind spot)
**Category:** 10 (Tests / TDD)
**Issue:** all 5 new clinics test suites that touch the service use `AsyncMock` repos + mocked audit writer. They correctly cover orchestration (RBAC, fiscal/specialty validation, event emission, 404), but **none exercises the real commit lifecycle** — which is why C9-1 was invisible. The green suite gave false confidence.
**Fix:** the integration test from C9-1 closes this; additionally consider one real-session test for `update_account` + `update_specialties` atomicity.

### info — C9-3: `get_dpo` route does not guard `UUID(tenant_id)` ValueError
**File:** `account_router.py:272-303`. The other 3 routes wrap `UUID(tenant_id)` in try/except → 422 on malformed header; `get_dpo` does not, so a malformed `X-Tenant-ID` → unhandled `ValueError` → 500. Low impact (header is auth-injected in prod), but inconsistent. One-line fix: same try/except as siblings. Mechanical (Carril A candidate for the builder during the fix loop).

### info — F-RBAC-consistency (preload, confirmed): service-level check vs shared `Depends`
**File:** `clinic_account_service.py:47,164-165`. RBAC `_WRITE_ROLES={owner, admin_clinic}` is enforced fail-closed in the service (live-confirmed 403 for `doctor`), correctly aligned to the platform canonical `ALLOWED_BRAND_OWNER_ROLES` and to the `doctors_router` precedent (Chris #3b). The sibling pattern is a shared `Depends(require_brand_owner_access)`; this story checks in the service by hand. Functionally correct + fail-closed; the consistency/anti-dup refactor (route the check through the shared dependency) is a **next-story candidate**, not a blocker.

### info — C9-4: double `get_active_for_tenant` query in specialties-catalog route
**File:** `account_router.py:251-255` calls `get_active_for_tenant` then `service.get_specialties_catalog` which calls it again (`clinic_account_service.py:283`). Harmless duplicate query; trivial to collapse. Not blocking.

---

## Detailed Category Notes

**Cat 1 (DDD):** PASS. Domain (`clinic.py`, `events.py`, `exceptions.py`) is pure Python — only pydantic/dataclasses, zero sqlalchemy/fastapi (verified). Service has no HTTP imports. Router is thin (delegates, maps exceptions). Repos own persistence. The only divergence is the atomicity WARN (C1-2). `field_validator` back-compat coercion (commit 120f5390) is sound debugging discipline (a pre-existing test caught a real regression).

**Cat 2 (Tenant Isolation):** PASS, **live-confirmed**. Every `ClinicRepository` query filters `tenant_id` (incl. `get_by_id` dual-filter). `ClinicConfigRepository` filters `TenantModel.id == tenant_id` (the tenant PK IS the isolation key — correct). Cross-tenant PATCH/GET → **404 live** (no leak, not 403 — correct per RN-5). `get_by_slug_public` is intentionally tenant-less (public doctors endpoint, no PHI) — pre-existing, not this story.

**Cat 3 (Soft Deletes):** PASS. No hard deletes. `soft_delete` uses `update().values(deleted_at=func.now())`. All reads filter `deleted_at IS NULL`.

**Cat 5 (SQLA 2.0):** PASS. `select()`/`update()` idiom throughout, `await session.execute()`, `DateTime(timezone=True)` on timestamps. Model uses `Column()` style consistent with the existing file + engine models (architect-ratified — do NOT mix `mapped_column` into a `Column`-style file).

**Cat 7 (Pydantic v2 / PII):** PASS. All DTOs `ConfigDict(from_attributes=True)`. `response_model=` on all 4 routes (verified + arch gate green). `currency: str | None` present, no hardcoded `'USD'`. Clinic identity fields (`email`/`phone`/`address`/`fiscal_id`) appear in `ClinicAccountResponse` — these are the **tenant's own business contact data**, explicitly declared non-PHI (domain docstring + arch § Architecture Decisions); the authenticated admin views their own clinic. Masking would be nonsensical; justification is documented → **not a WARN**.

**Cat 8 (Migration):** PASS. `039` raw SQL `ADD COLUMN IF NOT EXISTS` ×7, no `op.create_table/add_column`, no `sa.Enum`, idempotent, safe `downgrade` with `IF EXISTS`. `down_revision="038_vitalia"`. Live: migration applied 038→039, 7 columns confirmed. Specialties = zero migration (JSONB engine, correct).

**Cat 11 (Cross-cutting):** PASS. UTC + `DateTime(timezone=True)`, no `datetime.utcnow()`. Currency nullable, no hardcode. Validator/catalog error messages Spanish neutro, no voseo ("no puede estar vacío", "debe tener N dígitos", "fuera del catálogo de …"). Commit bodies cite decisions honored (D3-revoked, Q1-Q4). Native-first commands. Commit pathspec discipline observed.

**Cat 12 (Mirror):** PASS. Scanned all 5 new basenames (`fiscal_id_validator`, `specialty_catalog`, `clinic_account_service`, `clinic_config_repository`, `account_router`) across comunify/nicolify/lupulo/core → **0 matches**. No cross-brand mirror. fiscal-validator + specialty-catalog correctly marked lift-candidates (documented, not lifted on first impl — correct per anti-duplication). `ClinicConfigRepository` does RMW on engine `TenantModel.config_json` JSONB via import (engine-boundary: consume read, replicate write brand-local — NO new engine column). Correct.

**Cat 13 (Connectivity / CONN):** PASS. **C**onsumed: FE config feature + (event) agents runtime. **O**n map: `cap_target: configuracion.cuenta` (`# cap:` headers present in all new files). **N**avigable: `/{tenantId}/config/cuenta` reachable via Ribbon Plataforma. **N**otarized: `account_router` mounted via `include_router(..., prefix="/api/v1/clinics/account")` at `main.py:104` — verified reachable, live 200/403/404/422.

## Downstream regression scope

| Surface modified | Downstream consumers | Status |
|---|---|---|
| `clinics/.../clinic_repository.py` (`get_active_for_tenant`, `update_account` NEW; existing methods unchanged) | `brand_studio/.../marca_service.py:144` (uses `get_active_for_tenant` with graceful fallback) | PASS — additive methods, no signature break; `language=None` back-compat fix (120f5390) protects this consumer |
| `clinics/domain/clinic.py` (+7 fields, +field_validator) | any `Clinic.model_validate` caller | PASS — fields nullable, validator coerces legacy None |
| `_shared/validation`, `_shared/catalogs` (NEW) | account_router only | PASS — no prior consumers |
| ENGINE (`core/luana-core-*/src/`) | n/a | NOT touched on BE-side — no engine downstream |

No cross-brand mirror (Cat 12 = 0). Spot-checked service+validator+router+cross-tenant suites → green.

## Contract Compliance (business surface)

- [x] All entities from arch § 1 implemented (Clinic +7 fields, ClinicSpecialtiesChanged event, exceptions)
- [x] All DTOs from arch § 3 match (4 DTOs; `SpecialtyCatalogResponse.specialties` evolved to `[{id,name,tier}]` rich shape per fix_session — ratified scope-delta, documented)
- [x] All routes from arch § 4 registered with `response_model=` (4 routes, verified)
- [x] Repository interfaces from § 6 fully implemented (`get_active_for_tenant`, `update_account`, `ClinicConfigRepository`)
- [x] arch § 8 Agentic Surfaces = N/A (no copilot/sales_agent) — correct
- [~] Test surfaces from § (Test Surfaces) present per layer — **EXCEPT** the audit-durability layer needs a real-session test (C10-1 / C9-1)
- [x] CONTRACT_PAIR registered in `test_fe_be_contract_parity.py` (HB-42) — present
- [ ] **DoD live-verify (auditable write):** NOT actually met — audit row does not persist (C9-1). `dod_evidence` is a false-positive.

## Allowlist Movement

- [x] No allowlist grew. No `KNOWN_*` ratchet entry added. (Shrink-only respected.)

## Native-First Audit

- [x] No `docker exec ... ruff|pytest|...` in commits (native venv used)
- [x] No `git add .` / `-A` / `-u` (commit pathspec)
- [x] No `--no-verify` / force-push / revert evidence

## Live-verify by auditor (mandatory write exercised)

| Action | Observed | Backend/DB effect |
|---|---|---|
| `PATCH /api/v1/clinics/account/ {legal_name:"AUDITOR-PROBE…"}` (owner) | HTTP 200, body reflects new legal_name | clinic field **persisted** ✓; `vitalia_audit_log action=clinic_account_patch` count = **0** ✗ (the defect) |
| `PATCH … role=doctor` | HTTP 403 "se requiere rol admin_clinic" | fail-closed ✓ |
| `GET … X-Tenant-ID=<other tenant>` | HTTP 404 "No se encontró la clínica" | no cross-tenant leak ✓ |
| `PATCH … {fiscal_id:"BADRFC"}` (MX) | HTTP 422 `{field:fiscal_id, message:"RFC inválido…"}` | validation + Spanish neutro ✓ |
| (restore) `PATCH {legal_name:"Sanaré LATAM S.A. de C.V."}` | HTTP 200 | dev DB restored ✓ |

## § Upstream deficiency (reflex — responsibilize upstream)

The audit-durability defect class (audit INSERT on a non-committing session, rolled back at close → HTTP 200 with no row) was **already discovered and fixed** for the CRM surface (`get_async_session_committing`, `src/db.py:73-95`, "Surfaced by live god-matrix verification"). It recurred here because:
1. **Architect** declared "audit log SYNC pre-response" + "same commit atomicity" in 03-arch § 7 but did NOT pin the *session dependency* (`get_async_session_committing`) as a wiring requirement in the ticket — leaving the builder free to mount the non-committing one.
2. **Builder/dev-team** signed `dod_evidence` off a structlog line (`audit_log_async_written`) instead of a committed-row query — the `verification-real-not-200` anti-pattern, on an auditable write.
3. **No test** exercised the real transaction lifecycle (mocked sessions throughout).

→ **Harness backlog (auto-captured):** propose an arch-fitness test that asserts any vitalia router writing `vitalia_audit_log` either uses `get_async_session_committing` or commits after the audit write (mechanical guard against this recurring a 3rd time). Will file HB entry + (pattern ≥2×) a tooling learning. Architect ticket template should pin the committing session dependency for any endpoint with a mandatory audit write.

## Verdict Math

- Cat 9 (Security / HIPAA-lite audit) **FAIL** (live-confirmed) → **overall FAIL** → **CHANGES_REQUESTED**.
- Routing: stake-asymmetric (compliance/audit) → Carril C' (auditor returns fix plan + regression-test design; does NOT self-patch). Builder applies Option A + integration test, re-runs gates, re-exercises live (audit row present), re-hands to auditor.
- All other categories PASS; 2 WARNs (atomicity C1-2 subsumed by the C9-1 fix; test blind spot C10-1 closed by the same regression test); 3 info (mechanical, fold into the fix loop).
- Live-verify floor: NOT met for the auditable-write requirement (`dod_live_verified` should revert to false until the audit row persists).

---

**Self-fix log:** none applied (the single blocker is a stake-asymmetric HIPAA-lite category → CHANGES_REQUESTED per v5, not Carril R/A). The auditor exercised the live write to confirm the defect rather than trusting the self-reported `dod_evidence`.

---

## Audit iteration 2 (re-audit, SCOPED to the C9-1 fix) — 2026-06-12

**Scope:** verify ONLY the C9-1 fix (Option A) + the folded info-fixes (C9-3, C9-4) + closure of WARNs C1-2 and C10-1. The other 10 categories were PASS in iter 1 and are NOT re-scored. Fix lives uncommitted in the working tree (4 files: `account_router.py`, `clinic_repository.py`, `clinic_config_repository.py` modified + `test_account_audit_durability.py` NEW).

**Verdict:** **APPROVED**

### What was verified (quirurgical — 4 items)

**1 — Diff correct + minimal + no broken callers.**
- `account_router._get_db`: `get_async_session` → `get_async_session_committing` (docstring states the C9-1 rationale + cites `marca_router.py` mirror). ✓ Exactly Option A.
- `ClinicRepository.update_account`: internal `commit()` → `flush()` (flush kept so the in-transaction re-fetch sees the UPDATE; commit deferred to caller). ✓
- `ClinicConfigRepository.update_specialties`: internal `commit()` removed. ✓
- **No other callers depend on the removed commits.** Grep confirmed: `update_account` → sole caller `clinic_account_service.py:193`; `update_specialties` → sole caller `clinic_account_service.py:201`; `ClinicConfigRepository` used only by the account service/router. The `create()` (`clinic_repository.py:143`) and `soft_delete()` (`:246`) commits are **intact** and belong to methods NOT in the `patch_account` path — verified by reading the file (lines 122-145 `create`, 227-247 `soft_delete`). No stray mid-transaction commit in the unit-of-work. ✓
- `patch_account` flow is now a clean single UoW: RBAC → fiscal validate (pre-persist, raises before any write) → specialty validate (pre-persist, line 188-189) → `update_account` (flush) → `update_specialties` (no commit) → `audit_writer.write` (INSERT, no commit) → return → committing-session commits all three atomically; any raise rolls back all three. ✓

**2 — Integration test is REAL and a genuine RED→GREEN guard (closes C10-1).**
- `test_account_audit_durability.py::test_patch_account_commits_audit_row` wires the real `account_router` + real repos + real `AsyncAuditWriter` (NO service/repo/audit mocks), inserts a real tenant+clinic via raw SQL, PATCHes via httpx ASGITransport, and asserts `SELECT COUNT(*) FROM vitalia_audit_log WHERE action='clinic_account_patch'` ≥ 1 **on the actual table** + `legal_name` persisted (atomicity). `@pytest.mark.integration` (auto-skip if PG down).
- **GREEN proven** against real `vitalia_test` DB: `1 passed` (not skipped). 
- **RED proven** by the auditor: temporarily neutralizing the committing semantics in the test's `_get_db` override → `AssertionError: assert 0 >= 1` while the `audit_log_async_written` **structlog line still fires** — reproducing exactly the structlog-≠-committed-row false-positive that shipped in iter 1. Restored → green. The test genuinely depends on the commit. ✓
- Minor fidelity note (non-blocking): the test overrides production `_get_db` with a local committing generator (documented workaround for a db.py singleton port-pollution issue), so it does not exercise the literal production `get_async_session_committing` wiring — but the auditor's own live-verify (item 3) covers the production wiring end-to-end. Together: sufficient.

**3 — Live-verify re-run by the AUDITOR (not trusting the self-report) against the running :8002 stack, tenant `e69a691d-070e-5caf-a053-6e74642ec100` (sanare-latam-mx, MX), clinic `f035be5b`:**

| Action | Observed | DB effect |
|---|---|---|
| `PATCH /account/ {legal_name:"AUDITOR-PROBE iter2…"}` (role owner) | HTTP 200, body reflects new legal_name | `vitalia_audit_log action=clinic_account_patch` count **1 → 2** (MY write incremented it); latest row `payload_redacted` decodes to `{"updated_fields":["legal_name"]}`, fresh `occurred_at 2026-06-12 01:36:58Z` ✓ **(the durable row, not a structlog line)** |
| `PATCH /account/ {legal_name:"SHOULD-NOT-PERSIST…", primary_specialties:["invalid-id-xyz"]}` | HTTP 422 `{field:primary_specialties, message:"Especialidades fuera del catálogo de MX: invalid-id-xyz"}` (Spanish neutro) | audit count stays **2** (NO increment) AND `legal_name` in DB still `AUDITOR-PROBE iter2…` — the valid `legal_name` in the same body did **NOT** leak through. **Atomicity live-confirmed: whole transaction rolls back as a unit.** ✓ |
| `GET /account/dpo` with `X-Tenant-ID: not-a-uuid` (C9-3) | HTTP 422 `{detail:"badly formed hexadecimal UUID string"}` (not 500) | guard works ✓ |
| `GET /account/specialties-catalog` (C9-4) | HTTP 200, rich `[{id,name,tier}]` shape, single query (`(country, entries)` tuple) | ✓ |
| (cleanup) `PATCH {legal_name:"Sanaré LATAM S.A. de C.V."}` | HTTP 200 | dev DB restored ✓ |

**4 — WARN C1-2 (atomicity) → CLOSED.** Resolved by Option A: validation is pre-persist and the three writes share one committing unit-of-work. Live-confirmed via the negative case above (valid `legal_name` did not persist when the sibling specialty validation failed). The partial-state hazard the WARN flagged is now structurally impossible.

### Gates re-run by the auditor (scoped to the changed surface)
- `ruff check` (clinics + tests) → **All checks passed**; `ruff format --check` → **64 files already formatted**.
- clinics suite (unit + the new integration test) → **all pass** (integration test ran, not skipped).
- arch gates: `test_response_model_required` + `test_audit_log_sync_write` → 10 passed; `-k "tenant_filter or migrations_idempotent"` → 72 passed. ✓
- Stack `:8002` health → 200.

> Note: `gate-output.json` in the folder is iter-1 (pre-fix, `vitalia_test`/`test-vitalia`). The auditor re-ran the relevant gates directly on the working-tree fix rather than trusting the stale JSON. A full `gate-runner` re-run on commit is recommended at merge (the fix is currently uncommitted).

### WARN / info status after iter 2
- **C9-1 (FAIL → RESOLVED):** audit row now persists durably (live count 1→2 by auditor's own write). The `dod_live_verified` floor for the auditable-write requirement is now genuinely met.
- **C1-2 (WARN → CLOSED):** single committing unit-of-work; atomicity live-confirmed (negative case).
- **C10-1 (WARN → CLOSED):** real-session regression test added, RED→GREEN proven by auditor.
- **C9-3 (info → CLOSED):** `/dpo` UUID guard → 422 (live).
- **C9-4 (info → CLOSED):** double query collapsed (live).
- **F-RBAC-consistency (info → remains):** service-level RBAC check vs shared `Depends` — still a next-story refactor candidate, not a blocker (functionally fail-closed, live-confirmed in iter 1).
- **Structural note (carried to next story, non-blocking):** `create`/`soft_delete` still own their internal commits. Fine for now (each is a standalone op with no composing caller); migrating the whole clinics repo to caller-owned commit remains the cleaner end-state.

### Verdict math (iter 2)
- C9-1 (Cat 9 / HIPAA-lite audit): **PASS** (was the sole FAIL) — live-confirmed durable audit row + atomic rollback.
- 0 FAIL · 0 open WARN (both closed) · 0 open info blocker. Diff minimal, no broken callers, real regression guard RED→GREEN, auditor exercised the critical write live (POST/PATCH + read logs + confirm DB effect + negative atomicity).
- **Overall: APPROVED.** Story may proceed to `/pm-vitalia` merge (Fase F) — commit the working-tree fix first; recommend a clean `gate-runner` pass on the committed SHA at merge.

**Self-fix log (iter 2):** none applied. The fix was authored by the builder per the iter-1 Carril C' plan (stake-asymmetric HIPAA-lite category — auditor does not self-patch compliance). The auditor independently verified the diff, proved the regression test RED→GREEN, and exercised the critical write live before signing off — not trusting the self-reported `dod_evidence`.
