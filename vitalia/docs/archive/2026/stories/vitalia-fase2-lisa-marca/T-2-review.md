<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# T-2 Code Review — BE `marca_router` 21 endpoints + 4 services + RBAC + audit_log

**Story:** vitalia-fase2-lisa-marca (F2-S7)
**Ticket:** T-2
**Brand:** vitalia
**Surface:** BE (21 endpoints + 4 services + 18 DTOs + RBAC + repos + persistence)
**State:** pushed
**Push commit SHA:** `1261f6dc3b488bc4cd6ffd4304d59ebb9c62c7ba`
**Auditor:** auditor-backend (Opus 4.7)
**Audit iter:** 1
**Audit date:** 2026-05-27T09:32:41Z

## Verdict: **FAIL**

The module is **broken at module load time**. The router file cannot even be imported in the running Python interpreter. Three production-blocking bugs combine into a single failure mode: (a) router imports names that do not exist; (b) router calls service methods with kwargs the service does not accept; (c) router is not registered in `main.py` nor in `extensions.py` so even when fixed it remains unreachable. None of these are caught by the existing gates because every gate (arch fitness, unit tests, lint, format, tsc) operates on static or mock-isolated surfaces.

**This is Case D escalation per `.claude/rules/auditor-self-fix-policy.md`** — multi-file structural fix (3+ files, branch logic, public API). NOT self-fix. Must spawn `/dev-team` Caso B auto-fix loop OR escalate Chris.

## Domains touched

- BE FastAPI routes (21 endpoints declared, 0 reachable)
- BE application services (4: MarcaService / VoicePreviewService / VoiceBlocklistService / TrustCatalogService)
- BE domain entities (4: prohibited_phrase / archetype / voice_preview / trust_signal)
- BE persistence model (`prohibited_phrase_model.py`)
- BE infrastructure repos (ABCs + impls for prohibited_phrase + trust_signal)
- BE API DTOs (18 Pydantic v2 DTOs)
- BE `_shared/auth/rbac.py` MODIFY (added `require_brand_owner_access()` factory)

## Skills consulted

- `backend-expert` + `references/runtime-quality-checklist.md`
- `brand-expert` (PersonalityProfile compiler v2 + 4 Jung archetypes salud)
- `offer-expert` / `offer-type-preset-expert` — n/a (no offer surface)
- `metrics-expert` — n/a (no analytics surface)
- `tessl__fastapi` (response_model + Annotated deps + Depends factory)
- `tessl__pytest-api-testing` (n/a — tests in T-3)
- `tessl__graceful-degradation` (voice_preview cache fallback, audit log sync_write)
- `.claude/rules/backend-ddd.md` (Inside-Out, no cross-module)
- `.claude/rules/tenant-isolation.md` (every query filters tenant_id)
- `.claude/rules/anti-duplication.md` (engine consume via import; no mirror)
- `.claude/rules/sales-agent-brand-voice.md` (D2 anti-creep cardinal)
- `vitalia/.claude/rules/hipaa-lite.md` (brand_studio is owner-config — no PHI dual filter)
- `vitalia/.claude/rules/shell-feature-architecture-mandatory.md` (ADR-vitalia-004 § 5-6 BE)

## Gate Status (from `gate-output.json` iter 1)

| # | Gate | Result | Auditor commentary |
|---|---|---|---|
| 1 | ruff (lint) | PASS | confirms 0 syntax errors — does NOT execute imports |
| 2 | ruff (format) | PASS | format-only — does NOT exercise runtime |
| 3 | pytest arch fitness | PASS | **AST scan only — never imports the router** |
| 4 | pytest brand_studio unit | PASS (58) | 58 tests pass via mocks; **0 tests import `marca_router`** |
| 5 | tsc | PASS | n/a for BE |
| 6 | eslint | PASS | n/a for BE |
| 7 | vitest | WARN | n/a for BE |
| 8 | playwright syntax | PASS | n/a for BE |

> **Critical observation:** `gate-output.json::any_fail=false` is **technically true but operationally misleading**. The gate suite does not validate that the router module imports successfully or is mounted on the FastAPI app. Any consumer of T-2 deliverables (T-4 FE which calls `/api/v1/lisa/marca/initial-state/...`) will receive a 404 — the route simply does not exist on the running server.

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | Inside-Out layers correctly arranged; arch fitness `test_brand_studio_module_ddd.py` passes |
| 2 | Tenant Isolation | PASS | `prohibited_phrase_repository_impl.py:74-83` filters `tenant_id` + `IS NULL` seed exception; `trust_signal_repository_impl.py:82` queries `TenantModel.id == tenant_id` |
| 3 | Soft Deletes | PASS | `deleted_at` column + `where(...deleted_at.is_(None))` everywhere; `soft_delete()` uses `update().values(deleted_at=now)` |
| 4 | Code Quality | WARN | ruff GREEN; `# noqa: SLF001` for private-attribute access in router (anti-pattern); ~25 `try: ... except ValueError as exc: raise HTTPException(422)` blocks could be reduced via a dep factory |
| 5 | SQLAlchemy 2.0 | PASS | `select()`, `mapped_column()`, `Mapped[]` everywhere; `AsyncSession.execute()` + `.scalars()` |
| 6 | Async Consistency | PASS | Every route and service is `async def`; engine sync repos bridged via `session.run_sync()` (correct pattern) |
| 7 | Pydantic v2 / PII | PASS | `ConfigDict(from_attributes=True)` for responses, `ConfigDict(extra="forbid")` for patches; `response_model=` on all 21 routes; `model_validate()` not used (no `from_orm()` legacy) |
| 8 | Migration Quality | n/a | T-1 ticket |
| 9 | Security | PASS | RBAC dependency factory `require_brand_owner_access()` denies non-owner roles 403; no PHI in this module (owner-config) per `hipaa-lite.md` |
| 10 | Tests / TDD | FAIL | 9 of T-3's 18 declared test files are MISSING (see Finding F3); validators referenced in 04-validators.yaml point to non-existent files |
| 11 | Cross-cutting | WARN | `datetime.utcnow()` in 2 domain entities (master-data violation — also flagged in T-1 review) |
| 12 | Mirror detection | PASS | Engine `luana_core_brand_studio` consumed via import only; no cross-brand mirror; ABC + impl pattern correct |

## Findings

### **FAIL: F1 — Router module unloadable: `ImportError` at module init**

**Category:** 1 (DDD compliance) + 4 (Code Quality) — **production-blocking**
**File:** `vitalia/backend/src/modules/vitalia/brand_studio/api/routers/marca_router.py:82-87`
**Evidence:**

```python
from src.modules.vitalia.brand_studio.infrastructure.repositories.prohibited_phrase_repository_impl import (
    SqlaProhibitedPhraseRepository,        # ← class does not exist
)
from src.modules.vitalia.brand_studio.infrastructure.repositories.trust_signal_repository_impl import (
    SqlaTrustSignalRepository,             # ← class does not exist
)
```

The actual class declarations are:
- `vitalia/backend/src/modules/vitalia/brand_studio/infrastructure/repositories/prohibited_phrase_repository_impl.py:45` → `class ProhibitedPhraseRepositoryImpl(ProhibitedPhraseRepository):`
- `vitalia/backend/src/modules/vitalia/brand_studio/infrastructure/repositories/trust_signal_repository_impl.py:63` → `class TrustSignalRepositoryImpl(TrustSignalRepository):`

Verified empirically:

```
$ cd vitalia/backend && .venv/bin/python -c "from src.modules.vitalia.brand_studio.api.routers.marca_router import router"
ImportError: cannot import name 'SqlaProhibitedPhraseRepository' from
'src.modules.vitalia.brand_studio.infrastructure.repositories.prohibited_phrase_repository_impl'
(... /prohibited_phrase_repository_impl.py). Did you mean: 'ProhibitedPhraseRepository'?
```

This is why every smoke test silently "passes" — no test ever executes `from ...marca_router import router`. Arch fitness scans the SOURCE file via AST; it never tries to load it.

**Fix (Case B — spawn dev-team):** either (a) rename the impl classes to `SqlaProhibitedPhraseRepository` / `SqlaTrustSignalRepository`, or (b) fix the imports to use `ProhibitedPhraseRepositoryImpl` / `TrustSignalRepositoryImpl`. Builder choice. Both touch ≥3 files (router + 2 impl + tests that reference them).

**Skill ref:** `backend-expert/references/runtime-quality-checklist.md`. Specifically the "FastAPI Annotated dep type alias" and route registration sections.

### **FAIL: F2 — Router → Service signature mismatch on 7 GET endpoints**

**Category:** 1 (DDD compliance) + 4 (Code Quality) — **production-blocking**
**File:** `vitalia/backend/src/modules/vitalia/brand_studio/api/routers/marca_router.py:201, 254, 392, 445, 499, 529, 560, 665`
**Evidence:**

Router invokes:
```python
return await svc.get_identity(tenant_id=tenant_uuid, user_id=user_uuid)
return await svc.get_visuals(tenant_id=tenant_uuid, user_id=user_uuid)
return await svc.get_personality(tenant_id=tenant_uuid, user_id=user_uuid)
return await svc.get_contact(tenant_id=tenant_uuid, user_id=user_uuid)
return await svc.get_clinic_config(tenant_id=tenant_uuid, user_id=user_uuid)
return await svc.get_voice_preview(tenant_id=tenant_uuid, user_id=user_uuid)
return await svc.get_team_preview(tenant_id=tenant_uuid, user_id=user_uuid, limit=limit)
return await svc.get_trust_signals(tenant_id=tenant_uuid, user_id=user_uuid)
```

But service signatures (verified via `inspect.signature`):

```
get_identity:        (self, *, tenant_id: 'UUID') -> 'BrandIdentityDTO'
get_visuals:         (self, *, tenant_id: 'UUID') -> 'BrandVisualsDTO'
get_personality:     (self, *, tenant_id: 'UUID') -> 'BrandPersonalityDTO'
get_contact:         (self, *, tenant_id: 'UUID') -> 'BrandContactDTO'
get_clinic_config:   (self, *, tenant_id: 'UUID') -> 'ClinicConfigDTO'
get_voice_preview:   (self, *, tenant_id: 'UUID') -> 'VoicePreviewDTO'
get_team_preview:    (self, *, tenant_id: 'UUID', limit: int = 3) -> 'BrandTeamPreviewDTO'
```

Result at first request: `TypeError: get_identity() got an unexpected keyword argument 'user_id'`.

**Fix (Case B — spawn dev-team):** either (a) extend service signatures to accept `user_id: UUID` (preferred — needed for read audit_log per HIPAA-lite spec; `MarcaService.get_initial_state` already takes `user_id` and writes an audit row), or (b) drop `user_id=user_uuid` from the router invocations. Choice (a) is the spec-compliant fix because `03-arch.md § 5.2` requires audit row for every PHI/owner-config read (defense-in-depth per hipaa-lite.md § Audit log).

Also note: `get_trust_signals` signature DOES accept `user_id` (line 833 of marca_service.py) — that one call site is correct. So the inconsistency is half-applied.

**Skill ref:** `backend-expert` Inside-Out + DDD layers; `hipaa-lite.md` § Audit log mandatory PHI/owner-config reads.

### **FAIL: F3 — Router not registered in `main.py` nor `extensions.py` (21 endpoints unreachable)**

**Category:** 1 (DDD) + Acceptance contract — **production-blocking**
**Files:** `vitalia/backend/src/main.py`, `vitalia/backend/src/modules/vitalia/extensions.py`
**Evidence:**

```
$ grep -n "marca_router\|brand_studio" vitalia/backend/src/main.py
(no output)

$ grep -n "marca_router\|include_router.*brand_studio" vitalia/backend/src/modules/vitalia/extensions.py
(only string references in plan tier "brand_studio_simplified" feature list — NOT a router include)
```

Per `06-tickets.yaml::T-2.deliverables`:
> `vitalia/backend/src/main.py (MODIFY — include new router)`
> `vitalia/backend/src/modules/vitalia/extensions.py (MODIFY — register brand_studio router via include_router)`

Neither deliverable was met. The 21 endpoints exist as a module but are not mounted on the FastAPI app. T-2 impl-log § "Iter 3 — GREEN phase API" claims "Registered router in main.py" — that claim is false.

**Fix (Case B — spawn dev-team):** add `app.include_router(marca_router, prefix="/api/v1/lisa/marca")` to `main.py` after the existing `agenda_router` mount. Verify with `curl http://localhost:8002/api/v1/lisa/marca/clinic-config` → 200 (with valid headers).

**Skill ref:** `tessl__fastapi` § "Mounting routers"; ticket deliverable contract.

### FAIL: F4 — 9 declared test files do not exist (T-2 acceptance verifiers broken)

**Category:** 10 (Tests / TDD) — **acceptance gate failure**
**File:** `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/06-tickets.yaml::T-2.acceptance.A8`
**Issue:** `06-tickets.yaml::T-2.acceptance.A8` verifier executes
```
cd vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/brand_studio/test_marca_cross_tenant.py -v
```
That file does not exist on disk. The file `test_cross_tenant.py` (without the `marca_` prefix) exists instead, contributed by T-3. Also missing (referenced in T-2 acceptance A6/A4):
- `test_marca_router_visuals.py` (A6 verifier)
- `test_marca_service.py` (T-2 quality_gate `be_unit_marca_service`)
- `test_voice_preview_service.py` PASSED but covers VoicePreviewService not MarcaService

The full list of missing tests (declared in T-3 `06-tickets.yaml` deliverables) overlaps with T-2 acceptance:
- `test_prohibited_phrase_domain.py`, `test_voice_preview_domain.py`, `test_prohibited_phrase_repository.py`, `test_trust_signal_repository.py`, `test_marca_service.py`, `test_voice_blocklist_service.py`, `test_marca_router_identity.py`, `test_marca_router_visuals.py`, `test_marca_router_personality.py`, `test_marca_router_contact.py`, `test_marca_router_voice_preview.py`, `test_marca_router_trust_signals.py`, `test_marca_cross_tenant.py`, `test_growth_studio_event_no_phi.py` (EXTEND).

**Fix:** spawn `/dev-team` to either create the test files OR update `04-validators.yaml` + `06-tickets.yaml::T-2.acceptance` to reference the test files that actually exist (`test_cross_tenant.py`, `test_voice_warning_audit_log.py`, etc.). The acceptance contract is currently un-executable.

**Skill ref:** `.claude/rules/tdd-mandatory.md` (RED→GREEN per layer); `tessl__pytest-api-testing`.

### WARN: F5 — `VoiceBlocklistService.log_warning_override` returns `tenant_id` as `audit_id` sentinel

**Category:** 4 (Code Quality) + 11 (Cross-cutting)
**File:** `vitalia/backend/src/modules/vitalia/brand_studio/application/services/voice_blocklist_service.py:128`
**Issue:**

```python
return tenant_id  # audit_id returned as sentinel (actual UUID from DB)
```

The router (`marca_router.py:639`) exposes the value as `{"audit_id": str(audit_id)}` in the response. Callers (FE) will mis-interpret the returned UUID as the audit row ID when it is actually the tenant UUID. This is a misleading API contract.

**Fix (Case C — self-fix candidate? NO — touches contract):** either (a) have `AsyncAuditWriter.write()` return the audit row UUID and propagate it back to caller, or (b) drop `audit_id` from the response DTO and return `204 No Content` or `{"ok": true}`. Spawn `/dev-team` because it touches: audit_writer interface + voice_blocklist_service + router DTO + tests.

**Skill ref:** `backend-expert`; `hipaa-lite.md` § Audit log.

### WARN: F6 — Private attribute access from router layer (DDD smell)

**Category:** 4 (Code Quality) + 1 (DDD)
**File:** `vitalia/backend/src/modules/vitalia/brand_studio/api/routers/marca_router.py:590, 620`
**Issue:**

```python
svc = _build_service(session)
voice_blocklist_svc = svc._voice_blocklist  # noqa: SLF001 — same DI tree
```

The router reaches into `MarcaService`'s private attribute (`_voice_blocklist`) instead of either (a) keeping the `VoiceBlocklistService` reference from the `_build_service` factory or (b) exposing a public method on `MarcaService` that delegates. The `noqa: SLF001` confirms the builder knew it was an anti-pattern.

**Fix (Case C whitelisted — small refactor 1 file, 4 lines):** modify `_build_service` to return a tuple/NamedTuple of `(marca_service, voice_blocklist_service, trust_catalog_service)`. Replace 2 callsites in `marca_router.py`. ~12 lines total. **Defer to Case B alongside F1/F2/F3 since dev-team is already spawned for this ticket.**

**Skill ref:** `backend-expert/references/architecture-rules.md`; `.claude/rules/backend-ddd.md` § Inside-Out.

### WARN: F7 — `_NULL_CLINIC_ID = UUID(int=0)` sentinel pattern (HIPAA-lite drift candidate)

**Category:** 9 (Security) + 11 (Cross-cutting)
**File:** `vitalia/backend/src/modules/vitalia/brand_studio/application/services/{marca_service.py:67, voice_blocklist_service.py:31}` and `marca_router.py:92`
**Issue:** brand_studio is correctly classified as owner-config (no PHI). `hipaa-lite.md` § Tenant isolation says "Además de `tenant_id`, vitalia agrega `clinic_id` como segundo filter obligatorio en queries PHI". This module is exempt because there is NO PHI. The use of `UUID(int=0)` sentinel for audit row `clinic_id` column is reasonable but introduces an unindexed magic value into `audit_log` rows. If future analytics aggregates audit rows per clinic, this sentinel will pollute the result.

**Fix (info-only):** consider whether `audit_log.clinic_id` should be `nullable=True` and accept `None` for owner-level audit rows instead of `UUID(int=0)`. Schema-level change — spawn `/dev-team` if accepted. Otherwise document the sentinel convention in `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` § audit_log schema so future consumers exclude it from clinic aggregations.

**Skill ref:** `hipaa-lite.md` § Audit log columns.

### WARN: F8 — `datetime.utcnow()` deprecation in 2 domain entities (also flagged in T-1 review)

**Category:** 11 (Cross-cutting — `master-data.md`)
**Files:** `vitalia/backend/src/modules/vitalia/brand_studio/domain/prohibited_phrase.py:46`; `vitalia/backend/src/modules/vitalia/brand_studio/domain/trust_signal.py:32`
**Issue:** Same as T-1 review § F1. Replace `default_factory=datetime.utcnow` → `default_factory=lambda: datetime.now(timezone.utc)`. Whitelist item 14 self-fix candidate.

### info: F9 — Repository docstring inconsistency

**Category:** 4 (Code Quality)
**File:** `vitalia/backend/src/modules/vitalia/brand_studio/infrastructure/repositories/trust_signal_repository_impl.py:1-8`
**Issue:** Module docstring says "Stores via JSONB in tenant.config_json", but it actually stores in `tenant.config_json['vitalia_trust_signals']` per `_CONFIG_KEY = "vitalia_trust_signals"` (line 28). Doc string drift.

**Fix:** minor docstring tighten — non-blocking.

## Contract Compliance (T-2 deliverables vs `06-tickets.yaml::T-2`)

- [x] domain entities created — `prohibited_phrase.py`, `archetype.py`, `voice_preview.py`, `trust_signal.py` ✅
- [x] persistence model created — `prohibited_phrase_model.py` ✅
- [x] repository ABCs created — `prohibited_phrase_repository.py`, `trust_signal_repository.py` ✅
- [x] repository impls created — but **named differently than router expects** (F1) ⚠
- [x] `marca_service.py` orchestrator created — but **GET methods missing `user_id` param** (F2) ⚠
- [x] `voice_preview_service.py` LRU cache implemented ✅ (cache key correct per OQ-C)
- [x] `voice_blocklist_service.py` CRUD + log_warning_override ✅ (F5 warn on audit_id sentinel)
- [x] `trust_catalog_service.py` PE seed 8 entries ✅ (DIGESA, MINSA, SUSALUD, COP_ODONTO, CMP, SUNAT, ISO_9001, ESSALUD verified)
- [x] `marca_router.py` 21 endpoints with `response_model=` ✅ AST-verified (but broken runtime — F1+F2)
- [x] `marca_dtos.py` 18 Pydantic v2 DTOs ✅ (`ConfigDict(from_attributes=True)` + `ConfigDict(extra="forbid")` correctly applied)
- [x] `_shared/auth/rbac.py` MODIFY — `require_brand_owner_access()` factory added ✅
- [ ] `extensions.py` MODIFY — register brand_studio router ❌ **NOT DONE** (F3)
- [ ] `main.py` MODIFY — include new router ❌ **NOT DONE** (F3)

## T-2 Acceptance vs reality

| AC | Description | Reality |
|---|---|---|
| A1 | 21 endpoints declared with `response_model=` | PASS (AST scan) — but router unloadable (F1) |
| A2 | All PATCH/POST/DELETE have `@Depends(require_brand_owner_access())` | PASS (verified grep — 11 mutation endpoints use `_brand_owner_required`) |
| A3 | MarcaService writes audit_log row pre-response | PASS for mutations (`patch_identity`, `patch_visuals`, `patch_personality`, `patch_contact`); `get_initial_state` also writes audit. GET methods (single-resource reads) currently do NOT write audit row — may or may not be required by spec; revisit per F2 fix |
| A4 | VoicePreviewService cache key invariant | PASS (lines 37-50 build key from `(tenant_id, profile_id, compiler_version, blocks_hash)`); cache invalidation on `patch_personality` verified |
| A5 | TrustCatalogService PE seed = 8 entries | PASS (verified DIGESA/MINSA/SUSALUD/COP_ODONTO/CMP/SUNAT/ISO_9001/ESSALUD) |
| A6 | Logo upload ≤5MB + format whitelist | PASS (router lines 309-320) — note verifier cmd references `test_marca_router_visuals.py` which does NOT exist (F4) |
| A7 | No `health_voice_validator.py` created | PASS (arch test `test_no_health_voice_validator.py` 3/3 GREEN) |
| A8 | Cross-tenant PATCH returns 403 + audit row | FAIL — verifier file `test_marca_cross_tenant.py` does NOT exist (F4); coverage exists in `test_cross_tenant.py` but acceptance cmd is broken |

## Allowlist Movement
- Architecture fitness allowlists DID NOT GROW. ✅ (no new entries in `KNOWN_*` frozensets across the 5 brand_studio arch tests)
- `_KNOWN_EVENT_NAMES` extended from 7 → 22 events (15 added) — content-level whitelist, not arch ratchet; documented in 03-arch § 10.2.

## Native-First Audit
- [x] No `docker exec ... ruff|pytest` in T-2 commit
- [x] No `git add .` / `-A` / `-u` in commit body — only specific files staged
- [x] Commit body cites engine imports + anti-creep guards explicitly

## Cross-scope flags

None — T-2 is fully in BE scope. Zero edits to:
- `core/luana-core-*/src/` ✅ (verified via `git show 1261f6dc --stat`)
- `{other_brand}/` ✅
- `vitalia/frontend/` ✅
- `vitalia/.../copilot/` ✅
- `vitalia/.../sales_agent/` ✅

## Decisions honored (per `06-tickets.yaml::T-2.decisions_applicable`)

- [x] D1-arch: ADR-vitalia-004 § 5-6 (Backend DDD Inside-Out + audit log sync write) — DDD layout correct; audit log write present on mutations
- [x] D2-voice: NO `health_voice_validator.py`, NO `brand_voice_summary` mirror — ARCH TEST GREEN
- [x] D5-archetype: `BrandPersonalityDTO.archetype: Literal["caregiver", "sage", "healer", "hero"]` enum strict (omits Outlaw/Magician/Lover/Innocent) ✅ confirmed at `marca_dtos.py:97, 113`
- [x] OQ-A: `/initial-state/{subsubtab}` SSR endpoint declared ✅
- [x] OQ-B: 4 archetypes salud-friendly enforced via Pydantic Literal ✅
- [x] OQ-C: VoicePreviewService cache key `(tenant_id, profile_id, compiler_version, hash(blocks))` ✅
- [x] OQ-D: TrustCatalogService HYBRID_CATALOG dict with PE populated, AR/CL/CO/MX/BR empty ready for future stories ✅
- [x] OQ-E: BrandVoicePreview footer pattern — backend supports single endpoint `/voice-preview` returning 2 samples ✅
- [x] A2: No `PhiRepositoryBase` (owner config, no PHI) ✅
- [x] A3: LRU cache via in-process dict bounded 1000 (Redis tier deferred per future story) — partial vs spec but acceptable noted in voice_preview_service.py:32 comment
- [x] A4: `vitalia_prohibited_phrases` schema mirror in `prohibited_phrase_model.py` (per backend-ddd.md § schema-mirror exception) ✅
- [x] A10: audit_log sync_write per mutation — present on `patch_identity`/`patch_visuals`/`patch_personality`/`patch_contact`/`upload_logo`/`delete_logo`/`create_trust_signal`/`delete_trust_signal`/`get_initial_state`/`log_warning_override` ✅
- [x] A13: clinic_vertical read-only + edit-link to onboarding-clinica story ✅ (in `BrandIdentityDTO` and `ClinicConfigDTO`)

## Verdict Math

- **FAIL Cat 1+4 (F1)** — router unloadable. → overall FAIL.
- **FAIL Cat 1+4 (F2)** — service signature mismatch on 7 endpoints. → overall FAIL.
- **FAIL Cat 1+contract (F3)** — router not registered, 21 endpoints unreachable. → overall FAIL.
- **FAIL Cat 10 (F4)** — 9+ declared test files missing; acceptance verifiers broken. → overall FAIL.
- 4 additional WARNs (F5-F8) + 1 info (F9).
- Allowlist did not grow. → PASS gate.
- IMPL-LOG documents skills + decisions + Iter 3 claim "Registered router in main.py" is FALSE (impl-log integrity drift). → WARN for impl-log accuracy.

**Verdict: FAIL** — Caso B (spawn `/dev-team` auto-fix loop per `.claude/rules/auditor-self-fix-policy.md` § "Workflow Step 3 Caso B").

> Cap: this is iter 1. Remaining 2 iter before ESCALATE. Recommend `/dev-team` Caso B with explicit findings F1+F2+F3+F4 in handoff prompt. Self-fix Caso C inappropriate (>3 files, branch logic, public API change).

## Self-fix log

**NOT applied** — All findings are Caso B (structural / multi-file / contract) or Caso D (declared deliverables absent). Self-fix policy whitelist does not authorize:
- New file creation (test_marca_router_*.py)
- Branch logic change (router signature alignment with service)
- Public API change (router registration in main.py)

Auditor will NOT self-fix. Awaiting Chris ratify of FAIL verdict → spawn `/dev-team` Caso B with handoff prompt:

```
mode: AUDITOR_AUTO_FIX_LOOP
ticket: T-2
review: vitalia/docs/product/stories/vitalia-fase2-lisa-marca/T-2-review.md
findings: F1, F2, F3, F4, F5, F6, F8 (verbatim from review)
caps: 1 iter (audit cap = 3 total, this is post-iter-1)
deliverable: re-run be_arch_fitness + be_brand_studio_unit + import smoke test
  (cd vitalia/backend && .venv/bin/python -c "from src.main import app; print(len(app.routes))")
```

## Last iteration timestamp

2026-05-27T09:32:41Z (iter 1, audit-only — no commits made)
