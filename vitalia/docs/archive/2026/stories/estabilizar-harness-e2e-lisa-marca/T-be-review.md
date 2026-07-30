<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Backend Code Review: estabilizar-harness-e2e-lisa-marca (T-3 + T-5 BE surfaces)

**Date:** 2026-06-03
**PR / CONTRACT:** story `estabilizar-harness-e2e-lisa-marca` (bugfix, ADR-011), F2, module `brand_studio` (sub `lisa/marca`), cap `lisa-marca`
**Files Reviewed (in scope):** 3 named + 1 sanctioned new IAM resolver
- `vitalia/backend/src/modules/vitalia/brand_studio/application/services/marca_service.py` (T-5 logo storage + visuals coercion)
- `vitalia/backend/src/modules/vitalia/brand_studio/api/routers/marca_router.py` (T-3 X-User-ID optional + `_resolve_audit_actor`)
- `vitalia/backend/tests/modules/vitalia/brand_studio/test_marca_service.py`
- `vitalia/backend/src/modules/vitalia/iam/application/services/user_resolver.py` (NEW — sanctioned cross-module read, T-3 sub-bug #2b)
**Domains touched:** brand_studio (logo/visuals/personality/trust-signals routes), iam (audit-actor resolver)
**Skills consulted:** backend-expert (runtime quality, DDD, master-data), brand-expert (BrandVisuals/BrandIdentity aggregate shape), vitalia HIPAA-lite overlay (audit actor, dual-filter), anti-duplication (Cat 12 mirror scan)
**Verdict:** **APPROVED (WARN)**

## /test-vitalia Gate Status (consumed from gate-output.json, iter-1, exit 0, any_fail=false)

| Gate | Result | Detail |
|---|---|---|
| ruff check | PASS | All checks passed (0 errors) |
| ruff format --check | PASS | 1031 files, 0 reformats |
| pytest tests/architecture/ | PASS | 335 passed |
| pytest tests/modules/vitalia/brand_studio/ | PASS | 0 failed (skips on integration/eval markers) |
| tsc --noEmit | PASS | 0 errors |
| eslint src/ | PASS | 0 problems |
| vitest | PASS | 231 files, 2525 passed |

`mypy_strict` validator (04-validators L87, `mypy --strict marca_router.py`) was OMITTED from the scoped run — and is **not executable in this environment** (no `mypy` module in `.venv`). See finding W1 (a mypy-strict-only type concern that no runnable gate or existing test covers).

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 |
| 2 | Tenant Isolation | PASS | 0 |
| 3 | Soft Deletes | PASS | 0 |
| 4 | Code Quality | WARN | 1 (W1 mypy-strict arg-type) |
| 5 | SQLAlchemy 2.0 | PASS | 0 |
| 6 | Async Consistency | PASS | 0 (I1 informational) |
| 7 | Pydantic v2 / PII | PASS | 0 |
| 8 | Migration Quality | NA | 0 (no migration in scope) |
| 9 | Security | PASS | 0 |
| 10 | Tests / TDD | PASS | 0 |
| 11 | Cross-cutting | PASS | 0 |
| 12 | Mirror detection | WARN | 1 (W2 user_resolver async vs engine sync repo — lift candidate) |
| 13 | Connectivity / anti-isla | PASS | 0 |

## Cross-scope flags

NONE. No `core/` engine files touched by this story's commits (`5ef8cdd4`, `ea2bd5c0`, `c67bb62d`, `79139d1f`) — engine boundary respected (consume-only of `luana_core_assets.infrastructure.storage` + `luana_core_brand_studio.domain.identity.BrandVisuals`). No copilot/sales_agent files. No cross-brand pollution. FE files (`IdentidadView`, `PresenciaView`, POMs, specs) are out of scope (T-1/T-2 → auditor-frontend).

## Findings

### PASS — Logo storage (T-5): consumes engine StorageStrategy directly, no `core/` edit
**Category:** 1 / 12 · **File:** `marca_service.py:1020-1090` (`upload_logo`), `:1100-1135` (`delete_logo`)
`upload_logo` now consumes `luana_core_assets.infrastructure.storage.get_storage_strategy().save(BytesIO(content), filename, f"{tenant_id}/logo")` directly (storage layer, no DB entity), returning the real `(storage_path, public_url)`. The `save()` signature is honored exactly (`base.py:23-41` → `tuple[storage_path, public_url]`). The decision to bypass `AssetsService.upload_asset` is **correct and well-documented** (Asset FK `assets.offer_id → products.id` requires tables vitalia never migrates → `NoReferencedTableError` 500). Persistence target corrected from the buggy top-level `settings.visuals` to `settings.identity.visuals` (the SSoT location read by `get_visuals` / written by `patch_visuals`). `delete_logo` derives the storage key from the stored public URL by stripping `R2_PUBLIC_URL`, wrapped in best-effort `try/except + structlog.warning` so cleanup never blocks the field-unset nor the HIPAA audit write. **anti-duplication OK** — consumes the engine, recreates nothing.

### PASS — Audit actor real (T-3): `_resolve_audit_actor` + sanctioned IAM resolver
**Category:** 1 / 2 / 9 · **File:** `marca_router.py:96-130` (`_resolve_audit_actor`), `iam/.../user_resolver.py`
`_resolve_audit_actor(session, user_id_header)` centralizes the if-UUID-else-resolve-clerk_id path (DRY across 9 auditing endpoints). UUID-parse fast path for legacy/internal callers; otherwise `resolve_user_uuid_from_clerk_id` (new public IAM app service) maps `clerk_id → users.id`; no match → 422. The new `user_resolver.py` import is a **sanctioned cross-module read** — `iam` is NOT in `brand_studio`'s `CROSS_MODULE_FORBIDDEN_PATTERNS` (`test_brand_studio_module_ddd.py:56`, which only forbids scheduling/payments/fiscal/crm). It is a public app service (no `_` prefix), not a private internal, mirroring the accepted precedent `ClinicResolver._resolve_user_uuid` the architect directed to CONSUME. **Tenant-isolation:** the `clerk_id` column is `unique=True` globally (`user_model.py:30`) — this is identity resolution (1:1), not a tenant-scoped data query; tenant/clinic isolation is enforced downstream in the audit writer + brand-settings repo. No leak risk.

### PASS — X-User-ID optional on read endpoints (T-3 sub-bug #1)
**Category:** 2 / 9 · **File:** `marca_router.py:621-635` (`get_prohibited_phrases`), `:704-723` (`get_trust_signals`), `:787-809` (`get_trust_catalog`)
`X-User-ID` changed from required `Header(alias=...)` to `Header(alias=..., default=None)` on three reads keyed by `tenant + country`, which write no audit row. `X-Tenant-ID` stays **required** (tenant-isolation intact — invalid tenant → 422 preserved). `get_prohibited_phrases` documents `del user_id  # accepted-but-unused` honestly. Matches the in-codebase precedent (`X-User-Role` optional via `default=` at `:181`). All routes keep `response_model=` (Cat 7 PASS — 100% coverage verified across 21 routes).

### PASS — visuals dict→BrandVisuals coercion (defensive, fixes a real 500)
**Category:** 1 · **File:** `marca_service.py:296-313` (`_coerce_visuals`)
`BrandIdentity.visuals` is a dynamic attribute that the brand repo reloads as a **dict** (JSON) → attribute access would `AttributeError → 500`. `_coerce_visuals` normalizes None/dict/object uniformly and is reused in `get_visuals`, `patch_visuals`, `upload_logo`, `delete_logo`. No engine coercion exists to consume (Cat 12 clean) — this is correct brand-local defensive handling.

### WARN — W1: `get_trust_signals` arg-type mismatch (mypy-strict only)
**Category:** 4 · **File:** `marca_router.py:723` → `marca_service.py:884-889`
Route line 723 passes `user_id=user_uuid` where `user_uuid: UUID | None`, but the service signature is `get_trust_signals(*, tenant_id: UUID, user_id: UUID)` (non-optional). The existing `# type: ignore[return-value]` suppresses only the *return* error, not the *arg* error — `mypy --strict` would raise `arg-type` (`"UUID | None"; expected "UUID"`). **Runtime is correct:** the service body (`:899`) filters by `tenant_id` only and never references `user_id` (no audit row for this read), so `None` is safe and there is NO tenant-isolation impact.
**Fix (mechanical):** widen the service signature to `user_id: UUID | None` + docstring note "None when read carries no actor". This is the honest type contract.
**Why not Carril A self-fix:** the verifying gate (`mypy --strict`) is not executable in this environment (no `mypy` in `.venv`) and no existing test exercises the `user_id=None` path (`test_get_trust_signals_returns_list` passes a UUID). Per `auditor-self-fix-policy.md` Carril A, a fix must be re-verified by re-running the gate; I cannot gate-verify here, so I hand it to the builder as advisory. Non-blocking (all runnable gates green; runtime correct).
**Skill ref:** backend-quality.md (mypy strict on 8 domains), 04-validators.yaml:87.

### WARN — W2: `user_resolver.py` re-queries clerk_id→users.id (lift candidate)
**Category:** 12 · **File:** `iam/.../user_resolver.py:39-58`
The resolver runs `select(UserModel.id).where(UserModel.clerk_id == clerk_id)` directly. The engine `core/luana-core-iam/.../user_repository.py:33` already has `UserRepository.get_by_clerk_id`. NOT a blocking mirror because: (a) the engine repo uses a **sync** `Session`, while this path is **async** (`AsyncSession`); (b) it mirrors the established vitalia precedent `ClinicResolver._resolve_user_uuid` (same async raw `select`), which the architect directed to CONSUME; (c) no cross-brand mirror exists (grep clean across core + nicolify/comunify/lupulo). **Recommendation (future, not this story):** a clerk_id→users.id resolution helper is a candidate to lift to `core/luana-core-iam` with an async variant via `/pm-luana` promotion gate, so vitalia (and future brands) consume one path instead of two async re-queries. Advisory only.

### INFO — I1: synchronous storage I/O inside async path (pre-existing engine convention)
**Category:** 6 · **File:** `marca_service.py:1038` (`storage.save`), `:1125` (`storage.delete`)
`storage.save`/`storage.delete` perform blocking I/O (`put_object` / `shutil.copyfileobj`) and are called synchronously inside `async def`. This is **identical to the engine's own** `AssetsService.upload_asset` (`assets_service.py:95` calls `self.storage.save(...)` sync). The blocking-in-async concern is a pre-existing engine-layer convention the builder consistently follows; it is out of scope for a brand story (would be an engine-level fix via promotion gate). No action required.

### INFO — I2: `logo_id` decorrelated from storage key (cosmetic)
**Category:** — · **File:** `marca_service.py:1037-1042`
`upload_logo` passes `filename=f"logo-{logo_id}.{ext}"`, but both `r2.save` and `local.save` discard the meaningful filename and mint their own `uuid4()`-based key (keeping only the extension). So the stored object key contains a random UUID, not `logo_id`. Round-trip is still correct (delete derives the key from the stored URL, not from `logo_id`), so this is purely cosmetic decorrelation. No action required.

## Contract Compliance (business surface only)

- [x] Audit-actor resolver implemented + reachable (`_resolve_audit_actor`, `resolve_user_uuid_from_clerk_id`)
- [x] All 21 routes registered with `response_model=` (router `include_router` from `main.py:89`, prefix `/api/v1/lisa/marca`)
- [x] CONTRACT § agentic surfaces: empty (no copilot/sales_agent) — no `[CROSS-SCOPE]` flag
- [x] Test surfaces from 04-validators present at app layer (`test_marca_service.py::TestMarcaServiceLogoUpload` 3 tests + `test_audit_actor_real.py` + `test_prohibited_phrases_optional_header.py` + `test_user_resolver.py`) — TDD RED→GREEN documented in T-3/T-5 impl-logs
- [x] SC-6 (audit actor real) + SC-7 (prohibited-phrases browser 200) validator_ids declared; gate suite GREEN; live-verify + demo_signoff Chris APPROVED 2026-06-03 (checkpoint `dod_live_verified: true`)
- [x] Architecture fitness allowlists: no growth in this story's BE diff (`test_public_doctors_allowlist.py` change belongs to a DIFFERENT story — `a4f7209a feat(vitalia/clinics)` — out of scope)

## Downstream regression scope

| Surface modified | Downstream test targets | gate-runner status |
|---|---|---|
| `brand_studio/.../marca_service.py` + `marca_router.py` | `tests/modules/vitalia/brand_studio/` (covered by scoped gate) + `tests/architecture/` (covered) | PASS (335 arch + brand_studio 0 failed) |
| `iam/.../user_resolver.py` (NEW) | `tests/modules/vitalia/iam/test_user_resolver.py` (covered by brand_studio+module scope) | PASS |

Surfaces are brand-local (no `shared/`, no `core/` consumer fan-out). `command_alias = test-vitalia` (BE arch + brand_studio module + FE full) covers the changed surfaces. No additional downstream gate-runner spawn required.

## Allowlist Movement
- [x] No allowlist GREW in this story's BE diff.
- [x] `KNOWN_CROSS_MODULE_EXCEPTIONS` remains `frozenset([])` — `iam` import is allowed by absence from `CROSS_MODULE_FORBIDDEN_PATTERNS`, not by allowlist addition.

## Native-First Audit
- [x] No `docker exec ... ruff|pytest|mypy` in commits (gate run native via `.venv/bin/`).
- [x] No `git add .` / `-A` / `-u` in this story's commits.
- [x] Not pushed to `main` (wip/vitalia).

## R24 / CONTEXT-BRIEF acceptance
- [x] `Validator pass:` populated (`CONTEXT-BRIEF-validation.md`, in-process adversarial probe).
- [x] `Faithfulness flag: partial` (NOT blocking); §11 MEDIUM items M1/M2/M3 cited. M3 (de-mock scope under-coverage of `trust-signals`/`contact`/`voice-preview`) is an FE-test completeness note (T-1 surface), out of this BE audit's scope — flagged to auditor-frontend.

## Verdict Math
- No FAIL in categories 1 / 2 / 8 / 9 / 12 / 13.
- No allowlist growth without justification.
- All runnable `/test-vitalia` gates PASS (exit 0).
- `IMPL-LOG § Skills Consulted`: T-3/T-5 impl-logs cite backend-expert + brand-expert + HIPAA-lite overlay (baseline + domain skill present). No external-call surface → graceful-degradation N/A (storage is consumed via engine, best-effort try/except already present on delete).
- Two category WARNs (Cat 4 W1, Cat 12 W2) → **overall WARN**, both non-blocking advisories. Runtime is correct; no security/tenant/PII/migration/engine violation.

**Net: APPROVED with WARN.** The two BE surfaces (T-3 audit-actor + optional-header, T-5 logo storage) are sound, engine-boundary-clean, tenant-safe, HIPAA-actor-correct, and test-covered. W1 (mypy-strict arg-type widening) + W2 (async resolver lift candidate) are advisory follow-ups for the builder / `/pm-luana`, not merge blockers.

<!-- @pm: REVIEW.md ready (verdict=WARN/APPROVED). Brand: vitalia. Cross-scope flags: 0. Engine-edit flags: 0. Cross-brand flags: 0. Next action: APPROVED — proceed to /pm-vitalia merge. W1 (mypy-strict arg-type on get_trust_signals service sig) + W2 (user_resolver async lift candidate) are non-blocking advisories; optionally hand W1 to builder as a 1-line type-widening before merge. -->
