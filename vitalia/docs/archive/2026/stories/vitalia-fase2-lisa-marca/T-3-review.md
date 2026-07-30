<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# T-3 Code Review — BE pytest dual-tenant + arch fitness creep guards

**Story:** vitalia-fase2-lisa-marca (F2-S7)
**Ticket:** T-3
**Brand:** vitalia
**Surface:** BE tests only (`production_code: false`)
**State:** pushed
**Push commit SHA:** `d324517a`
**Auditor:** auditor-backend (Opus 4.7)
**Audit iter:** 1
**Audit date:** 2026-05-27T09:32:41Z

## Verdict: **CHANGES_REQUESTED**

The 8 test files actually delivered (66 unit + 14 integration-skipped + 17 arch tests) are well-constructed: AsyncMock pattern is consistent, fixtures are scoped correctly, arch tests use AST parsing for anti-creep ratchets. **However:** the ticket deliverable list in `06-tickets.yaml::T-3.deliverables` declares 18 test files; only 8 were delivered. The 9-file gap means the acceptance verifier commands in `T-3.acceptance.A1` (`pytest tests/modules/vitalia/brand_studio/ -v`) pass trivially because the missing tests simply don't get discovered. The covered surface is partial.

The Cat 10 verdict cascades from T-2 (broken router/service contract — tests would fail at module import if they covered the broken paths). T-3 cannot be APPROVED until T-2 is fixed and the missing test files are produced.

This is **Case B (CHANGES_REQUESTED structural)** per `.claude/rules/auditor-self-fix-policy.md` — multi-file new-test creation is HARD BAN for self-fix (whitelist item explicitly excludes "Escribir nuevo test"). Must spawn `/dev-team` Caso B.

## Domains touched

- BE tests (`vitalia/backend/tests/modules/vitalia/brand_studio/`)
- BE architecture fitness (`vitalia/backend/tests/architecture/`)

## Skills consulted

- `backend-expert/references/runtime-quality-checklist.md` (AsyncMock pattern, fixture isolation)
- `tessl__pytest-api-testing` (AsyncSession fixtures, factory fixtures, parametrize for edge cases)
- `.claude/rules/tdd-mandatory.md` (RED→GREEN discipline)
- `.claude/rules/tenant-isolation.md` (cross-tenant 403 + audit row tests)
- `.claude/rules/sales-agent-brand-voice.md` (D2 anti-creep arch tests)
- `.claude/rules/anti-duplication.md` (brand-local check)
- `vitalia/.claude/rules/hipaa-lite.md` (audit_log_sync_write + RBAC strict)

## Gate Status (from `gate-output.json` iter 1)

| # | Gate | Result | Detail |
|---|---|---|---|
| 1 | ruff (lint) | PASS | 0 errors in test files |
| 2 | ruff (format) | PASS | 0 reformats |
| 3 | pytest arch fitness | PASS | 203 passed (3 new tests added by T-3 included in count) |
| 4 | pytest brand_studio unit | PASS | 58 passed (T-1 9 + T-3 65 minus integration skip 16); auditor empirical run: 66 passed, 14 skipped (Postgres down) |
| 5-8 | tsc / eslint / vitest / playwright | PASS / WARN | n/a for T-3 (FE tickets) |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | Tests respect layering — no production code touched |
| 2 | Tenant Isolation | PASS | `test_cross_tenant.py` asserts cache isolation + audit row tenant_id propagation |
| 3 | Soft Deletes | n/a | Tests verify behavior; no production data deletion |
| 4 | Code Quality | PASS | AsyncMock pattern consistent; fixtures scoped per test; `_PREVIEW_CACHE.clear()` autouse fixture prevents inter-test pollution (good) |
| 5 | SQLAlchemy 2.0 | n/a | Integration tests `@pytest.mark.integration` skipped (Postgres down) |
| 6 | Async Consistency | PASS | All test functions `async def` + `@pytest.mark.asyncio` |
| 7 | Pydantic v2 / PII | PASS | DTO construction in fixtures uses ConfigDict patterns correctly |
| 8 | Migration Quality | n/a | |
| 9 | Security | PASS | RBAC tests cover patient/doctor/empty role → 403 (`test_rbac_brand_owner.py`); audit row tests verify `tenant_id` propagation; no PHI in test fixtures |
| 10 | Tests / TDD | FAIL | 10 of 18 declared test files missing (see Finding F1) |
| 11 | Cross-cutting | PASS | No voseo in test microcopy; no hardcoded currency; uses `datetime.now(timezone.utc)` where applicable |
| 12 | Mirror detection | PASS | Tests are brand-local; no cross-brand mirror |

## Findings

### **FAIL: F1 — 10 of 18 declared test files MISSING (T-3 deliverable gap)**

**Category:** 10 (Tests / TDD)
**File:** `vitalia/docs/product/stories/vitalia-fase2-lisa-marca/06-tickets.yaml::T-3.deliverables`
**Issue:** ticket lists 18 test files; commit `d324517a --stat` shows only 8 created. Missing:

| Declared in T-3 deliverables | On disk? |
|---|---|
| `test_prohibited_phrase_domain.py` | ❌ |
| `test_voice_preview_domain.py` | ❌ |
| `test_prohibited_phrase_repository.py` | ❌ |
| `test_trust_signal_repository.py` | ❌ |
| `test_marca_service.py` | ❌ (T-2 quality_gate `be_unit_marca_service` references this) |
| `test_voice_blocklist_service.py` | ❌ (only `test_voice_warning_audit_log.py` exists, narrower scope) |
| `test_marca_router_identity.py` | ❌ |
| `test_marca_router_visuals.py` | ❌ (T-2 acceptance A6 verifier references this) |
| `test_marca_router_personality.py` | ❌ |
| `test_marca_router_contact.py` | ❌ |
| `test_marca_router_voice_preview.py` | ❌ |
| `test_marca_router_trust_signals.py` | ❌ |
| `test_marca_cross_tenant.py` | ❌ (T-2 acceptance A8 verifier references this; `test_cross_tenant.py` exists with different name) |
| `test_growth_studio_event_no_phi.py` (EXTEND) | ❌ verify EXTEND not applied — `test_growth_studio_event_no_phi` does not exist in T-3 commit |
| `test_prohibited_phrases_seed.py` | ✅ (delivered in T-1 commit `c4a4f8e9` — counts) |
| `test_prohibited_phrases_migration.py` | ✅ (T-1 commit) |
| `test_voice_warning_audit_log.py` | ✅ |
| `test_voice_preview_service.py` | ✅ |
| `test_trust_catalog_service.py` | ✅ |
| `test_rbac_brand_owner.py` | ✅ |
| `test_cross_tenant.py` | ✅ (renamed from declared `test_marca_cross_tenant.py`) |

10 missing → ~55% deliverable coverage. The router-level integration tests are the most critical absence; without them the broken router (F1/F2/F3 of T-2 review) goes undetected — exactly the failure mode we observed.

**Fix:** spawn `/dev-team` Caso B to create the 10 missing test files using:
1. `tessl__pytest-api-testing` patterns for FastAPI `httpx.AsyncClient` integration tests.
2. Real router import (will fail until T-2 F1+F2+F3 are fixed — natural TDD RED).
3. Cross-tenant assertions: tenant_A request with `X-Tenant-ID: tenant_B_uuid` → 403 + audit row created.
4. Rename `test_cross_tenant.py` → `test_marca_cross_tenant.py` to align with T-2 acceptance A8 verifier OR update T-2.acceptance.A8 cmd to reference `test_cross_tenant.py`.

**Skill ref:** `tessl__pytest-api-testing`; `.claude/rules/tdd-mandatory.md` § "Tests RED first"; T-2 review § F4 (cross-link).

### WARN: F2 — Integration tests skipped (Postgres dependency)

**Category:** 10 (Tests)
**File:** `vitalia/backend/tests/modules/vitalia/brand_studio/test_prohibited_phrases_migration.py`, `test_prohibited_phrases_seed.py`
**Issue:** 14 integration tests carry `@pytest.mark.integration` and are SKIPPED in current gate run (Postgres down per gate-output.json notes). T-3 acceptance A1+A2+A3+A4 cannot be empirically verified offline.

**Fix:** non-blocking; gate runner must re-execute with `--marker integration` once Postgres up. `/pm-vitalia` should schedule this before Fase F merge transitions.

### info: F3 — `test_cross_tenant.py` could benefit from a real DB integration variant

**Category:** 10 (Tests)
**File:** `vitalia/backend/tests/modules/vitalia/brand_studio/test_cross_tenant.py`
**Issue:** Current cross-tenant tests use AsyncMock for repos. While `TestRBACCrossRoleIsolation` correctly exercises the dependency factory, the cross-tenant SQL filter behavior is only validated by mock-call kwargs assertion (`call_kwargs["tenant_id"] == tenant_a`). The actual SQL with `WHERE tenant_id = ...` against a real PG instance is not exercised.

**Fix (info):** future story should add `@pytest.mark.integration` variant that seeds 2 tenants and verifies tenant_A request returns 0 rows for tenant_B's data. Non-blocking for this audit.

### info: F4 — Some test files use `<string>:10` warning location (warning origin obscured)

**Category:** 4 (Code Quality)
**Evidence:** pytest output shows
> `<string>:10: DeprecationWarning: datetime.datetime.utcnow() is deprecated...`
The `<string>:10` location means the deprecation triggers during dynamic eval (likely a `dataclass` default_factory invocation). Origin is one of the domain entities flagged in T-1 review F1 + T-2 review F8.

**Fix:** resolved by fixing T-1/T-2 F8 (`datetime.utcnow` → `datetime.now(timezone.utc)`). No T-3-scoped change required.

## Test quality highlights (positive observations)

The 8 test files actually delivered are GOOD:

- **`test_cross_tenant.py`** (10 tests) — uses `_PREVIEW_CACHE.clear()` autouse fixture; cache isolation assertion is the most important property and correctly validated.
- **`test_voice_preview_service.py`** (13 tests) — covers cache HIT/MISS, LRU eviction at 1000, deterministic hash, invalidation. Comprehensive.
- **`test_trust_catalog_service.py`** (15 tests) — PE seed 8 entries verified; case-insensitive country lookup; unknown country returns empty.
- **`test_rbac_brand_owner.py`** (16 tests) — owner / admin_clinic / patient / doctor / empty role variants. The arch test perspective complements the brand-owner dependency.
- **`test_voice_warning_audit_log.py`** (12 tests) — audit row tenant_id propagation; payload structure verified.
- **`test_brand_studio_module_ddd.py`** (10 tests) — AST-based domain purity / infra forward-import / cross-module ban. Solid ratchet pattern (empty allowlists).
- **`test_no_health_voice_validator.py`** (3 tests) — file existence + class existence + import statement scan. Defense-in-depth.
- **`test_no_brand_voice_summary_table.py`** (4 tests) — migration scan + SQLA __tablename__ scan + class scan + AST import scan. Excellent anti-creep coverage.

Where the tests exist, they are well-constructed.

## Contract Compliance (T-3 deliverables vs `06-tickets.yaml::T-3`)

- [x] `test_brand_studio_module_ddd.py` ✅ (10 tests GREEN)
- [x] `test_no_health_voice_validator.py` ✅ (3 tests GREEN)
- [x] `test_no_brand_voice_summary_table.py` ✅ (4 tests GREEN — created not extended, but achieves same goal)
- [ ] `test_growth_studio_event_no_phi.py` EXTEND ❌ not visible in commit; test existed pre-T-3 and was NOT extended with 13 new events whitelist
- [ ] 10 test files missing per F1 above ❌

## T-3 Acceptance vs reality

| AC | Description | Reality |
|---|---|---|
| A1 | All BE unit + integration tests pass | PARTIAL — 66/80 pass, 14 skip (Postgres). Verifier cmd `pytest tests/modules/vitalia/brand_studio/ -v` runs only the 8 delivered files (66+14=80); the 10 missing files contribute 0 tests but verifier doesn't notice |
| A2 | Cross-tenant 403 + audit_log row test | FAIL — verifier cmd references `test_marca_cross_tenant.py` which does NOT exist (`test_cross_tenant.py` exists with different name) |
| A3 | Seed defaults PE test | PASS (test file exists, skipped on Postgres down — content correct) |
| A4 | Voice warning override → audit row | PASS (`test_voice_warning_audit_log.py` GREEN — 12 tests) |
| A5 | Creep guard arch tests | PASS (`test_no_health_voice_validator.py` + `test_no_brand_voice_summary_table.py` GREEN) |
| A6 | brand_studio DDD arch test | PASS (`test_brand_studio_module_ddd.py` 10 GREEN) |
| A7 | growth_studio_event_no_phi extended + 13 events validated | UNVERIFIED — extension not visible in T-3 commit; existing test pre-dates T-3 |

## Allowlist Movement

- 3 new arch tests added (test_brand_studio_module_ddd, test_no_health_voice_validator, test_no_brand_voice_summary_table). All ratchet patterns with EMPTY `KNOWN_*` frozensets — shrink-only ✅.
- No allowlist grew.

## Native-First Audit
- [x] Native venv used in T-3 commit `d324517a`
- [x] No `git add .` / `-A` / `-u` in commit
- [x] Conventional Commit format honored: `feat(vitalia/f2-s7): T-3 BE pytest dual-tenant + arch fitness creep guards`
- [x] `STORY_CLOSURE_GATE_SKIP=1` cited per parallel-safety M14 ratification

## Cross-scope flags

None — T-3 strictly in BE test scope. Zero edits to `core/`, other brands, frontend, copilot, sales_agent.

## Decisions honored (per `06-tickets.yaml::T-3.decisions_applicable`)

- [x] D2-voice anti-creep: 2 ratchets added (test_no_health_voice_validator + test_no_brand_voice_summary_table) ✅
- [x] A2: arch test verifies no `PhiRepositoryBase` consumed (DDD test enforces brand_studio infra layer) — implicit
- [x] A6: T-3 brings RBAC test coverage (`test_rbac_brand_owner.py` 16 tests)
- [x] A7: arch test `test_brand_studio_module_ddd.py::test_api_layer_uses_response_model` — local guard complementing the global `test_response_model_required.py`
- [x] A10: audit log sync write tests (`test_voice_warning_audit_log.py`) — partial coverage; mutation router tests missing (F1)

## Verdict Math

- **FAIL Cat 10 (F1)** — 10 of 18 declared test files missing; T-2 acceptance A6 + A8 verifiers reference files that don't exist. → overall FAIL.
- 0 FAILs in categories 1/2/8/9/12.
- 2 WARN + 2 info (F2/F3/F4).
- Allowlist did not grow (3 new arch tests with empty `KNOWN_*` frozensets) → PASS.
- IMPL-LOG (`T-3-impl-log.md`) cites skills consulted + 4 decision categories. → PASS.
- Builder cited `backend-expert/references/runtime-quality-checklist.md` in impl-log § "Skills Consulted". → PASS.
- 1 FAIL (F1) outweighs WARNs. → overall FAIL.

But severity: T-3 surface is "tests for things that already shipped under T-1/T-2". Cannot fix T-3 in isolation while T-2 router is broken (the missing tests would fail to import the broken router). T-3 fix is **coupled** to T-2 fix.

**Verdict: CHANGES_REQUESTED** (not FAIL, because:)
1. The 8 test files actually delivered are HIGH QUALITY and provide real coverage where they exist.
2. The 10 missing files are mostly router-integration tests that REQUIRE T-2 to be fixed first — fixing T-3 before T-2 is wasted work.
3. Caso B spawn for T-3 should be SEQUENCED AFTER T-2 Caso B fix.

> Cap: this is iter 1. Awaiting Chris ratify of CHANGES_REQUESTED → after T-2 fix, spawn `/dev-team` Caso B with handoff prompt:
> ```
> mode: AUDITOR_AUTO_FIX_LOOP
> ticket: T-3
> review: vitalia/docs/product/stories/vitalia-fase2-lisa-marca/T-3-review.md
> findings: F1 (10 missing test files; create router-integration suite + service unit tests)
> sequencing: AFTER T-2 fix lands (T-2 review F1+F2+F3+F4)
> deliverable: produce 10 declared test files; rename test_cross_tenant.py → test_marca_cross_tenant.py
> caps: 1 iter (audit cap = 3 total, this is post-iter-1)
> ```

## Self-fix log

**NOT applied** — Per `.claude/rules/auditor-self-fix-policy.md` NEVER list item 1: "Escribir nuevo test (cualquier `.test.*`, `.spec.*`, `test_*.py`) — TDD vive en dev-team". HARD BAN. Auditor MUST NOT create the missing test files.

Awaiting Chris ratify → `/dev-team` Caso B sequenced after T-2 fix.

## Last iteration timestamp

2026-05-27T09:32:41Z (iter 1, audit-only — no commits made)
