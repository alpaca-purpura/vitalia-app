# T-2 Result — camelCase alias en personality DTOs

**Story:** arreglar-guardado-voz-y-tono
**Ticket:** T-2
**Module:** brand_studio
**Commit:** 98a903a5
**Branch:** wip/vitalia

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | BE bugfix — DTO contract fix, runtime quality checklist | Pydantic v2 ConfigDict pattern, alias_generator=to_camel placement, no other DTOs touched |
| `tessl__fastapi` | FastAPI response serialization with by_alias | Confirmed FastAPI uses by_alias=True by default when alias_generator is set |
| `tessl__pytest-api-testing` | httpx.AsyncClient pattern, fixture scoping, integration mark | Used `@pytest.mark.integration` for route tests (auto-skip without Postgres, matches existing pattern) |
| `.claude/rules/tdd-mandatory.md` | TDD RED→GREEN order | Wrote RED test first (confirmed `soIDontSpeak` ValidationError), then applied fix |
| `.claude/rules/tenant-isolation.md` | Cross-tenant test requirement | Added §3 cross-tenant tests verifying service receives requesting tenant_id only |

---

## Technical Design

### Root cause (confirmed)
`BrandPersonalityPatchDTO` had `ConfigDict(extra="forbid")` only (no alias). Pydantic v2 with `extra="forbid"` treats unrecognized keys as extra — `soISpeak` is not a recognized snake_case field, so → `ValidationError extra_forbidden` → FastAPI returns 422.

`BrandPersonalityDTO` response had no `alias_generator` → FastAPI serialized with snake_case keys → FE read `so_i_speak` as `undefined` (expected `soISpeak`).

### Fix applied
Two DTOs in `vitalia/backend/src/modules/vitalia/brand_studio/api/dtos/marca_dtos.py`:

```python
# Import added (line ~18)
from pydantic.alias_generators import to_camel

# BrandPersonalityDTO (response)
model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)

# BrandPersonalityPatchDTO (request)
model_config = ConfigDict(extra="forbid", populate_by_name=True, alias_generator=to_camel)
```

`to_camel` maps: `so_i_speak↔soISpeak`, `so_i_dont_speak↔soIDontSpeak`, `identity_anchor↔identityAnchor`, `domain_context↔domainContext`, `technical_context↔technicalContext`, `format_instructions↔formatInstructions`, `personality_profile_id↔personalityProfileId`, `compiled_at↔compiledAt`, `compiler_version↔compilerVersion`, `tenant_id↔tenantId`. `archetype` unchanged.

`extra="forbid"` still blocks genuinely-extra fields (e.g. `bogusField`). `populate_by_name=True` keeps snake_case construction working (from_attributes, internal code, tests).

### NO other DTOs touched
As per T-2 scope: only `BrandPersonalityDTO` and `BrandPersonalityPatchDTO`.

---

## TDD Timeline

1. **RED** — Wrote `test_patch_personality_audit.py`, ran tests → `TestBrandPersonalityPatchDTOAlias::test_camel_case_so_i_dont_speak_accepted` FAILED with `ValidationError: Extra inputs are not permitted`. RED confirmed.
2. **Applied fix** — Added `to_camel` import + `populate_by_name=True, alias_generator=to_camel` to both DTOs.
3. **GREEN** — 16 DTO-unit tests PASSED, 8 integration tests SKIPPED (Postgres unavailable — same behavior as all existing router tests like `test_marca_router_personality.py`).

---

## Validators Run

| Validator | Command | Result |
|---|---|---|
| `be_patch_personality` (DTO-level) | `pytest tests/modules/vitalia/brand_studio/test_patch_personality_audit.py -v` | 16 PASSED, 8 SKIPPED (integration mark, Postgres down) |
| `be_lint` | `ruff check src/modules/vitalia/brand_studio/api/dtos/ tests/modules/vitalia/brand_studio/` | CLEAN |
| `be_lint` (format) | `ruff format --check src/modules/vitalia/brand_studio/api/dtos/` | CLEAN |
| `fe_typecheck` | `cd vitalia/frontend && npx tsc --noEmit` | CLEAN (FE untouched) |
| `be_arch_fitness` | `pytest tests/architecture/ -q` | 330 PASSED |

---

## LIVE Verification

Stack running on :8002. PATCH with camelCase body:

```bash
curl -X PATCH http://127.0.0.1:8002/api/v1/lisa/marca/personality \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000000" \
  -H "X-User-ID: 00000000-0000-0000-0000-000000000000" \
  -H "X-User-Role: owner" \
  -H "Content-Type: application/json" \
  -d '{"soISpeak":"hola"}'
```

**Result: HTTP 500** (not 422 extra_forbidden).

Backend logs confirm:
- No `extra_forbidden` error
- Field `soISpeak` parsed → reached service layer → `"fields_updated": ["so_i_speak"]`
- 500 is from audit log SQL issue (T-1 scope, pre-existing bug being fixed by T-1)

The FE↔BE contract for personality DTOs is repaired. The voice block field is accepted.

---

## Files Modified

| File | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/brand_studio/api/dtos/marca_dtos.py` | Added `from pydantic.alias_generators import to_camel`; updated `BrandPersonalityDTO.model_config` and `BrandPersonalityPatchDTO.model_config` with camelCase alias |
| `vitalia/backend/tests/modules/vitalia/brand_studio/test_patch_personality_audit.py` | NEW — 24 tests (16 DTO-unit + 8 integration-marked) |

---

## Notes

- Integration tests (§2/§3 HTTP + cross-tenant) are marked `@pytest.mark.integration` — they SKIP automatically when Postgres is unavailable, consistent with all existing route tests in `brand_studio/`. They will run against the stack in gate-runner if Postgres is up.
- Bidirectional validator pre-commit advisory: 1 HARD drift in cross_check_3 (e2e_test path). This is pre-existing from T-3 (E2E tests not yet written — T-3 depends on T-1 + T-2). Not introduced by T-2.
- T-1 (sanitize_payload fix) is a parallel ticket — its 500 on audit log is unrelated to T-2 scope.

---

## T-2.bis — _emit_telemetry forwards tenant_id to emit_event

**Ticket:** T-2.bis
**Commit:** 81b13787
**Branch:** wip/vitalia

### Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Runtime quality checklist pre-commit, async service pattern | Confirmed `_emit_telemetry` must be `async def` to `await` the async `emit_event` |
| `brand-expert` | Touching brand_studio module | No domain change — telemetry wiring only |
| `tessl__pytest-api-testing` | Unit test pattern with AsyncMock, no DB | Used `AsyncMock` for `GrowthStudioEmitter`, asserted `call_args.kwargs` |
| `.claude/rules/tdd-mandatory.md` | TDD order enforcement | RED test confirmed `TypeError: object NoneType can't be used in 'await' expression` before fix |
| `.claude/rules/test-design-doctrine.md` | Test design by nature of ticket (bug fix) | 4 unit tests: happy path, props isolation, user_id forwarding, exception swallow |

### Root Cause (confirmed)

`_emit_telemetry` was a `def` (sync) helper that called `self._telemetry.emit_event(...)` without:
1. `await` — `emit_event` is `async def`, so the call returned a coroutine that was immediately discarded
2. `tenant_id` kwarg — `GrowthStudioEmitter.emit_event(*, event_type, tenant_id: UUID, ...)` requires `tenant_id` as keyword-only

The bare `except Exception` caught the `TypeError` and logged `telemetry_emit_failed`, giving a 200 response but silently dropping every growth_studio telemetry event on brand_studio saves.

### Diff Summary

**`marca_service.py`:**
- `_emit_telemetry` changed from `def` to `async def` with explicit `tenant_id: UUID` + `user_id: UUID | None = None` kwargs
- Call site: `await self._telemetry.emit_event(event_type=..., tenant_id=tenant_id, user_id=user_id, props=props)`
- 6 caller sites updated with `await` + `tenant_id=tenant_id` + `user_id=user_id`:
  - `patch_identity` (line ~253)
  - `patch_visuals` (line ~354)
  - `patch_personality` (line ~501)
  - `patch_contact` (line ~600)
  - `create_trust_signal` (line ~903) — already had `tenant_id=tenant_id, user_id=user_id` in `**props`; now correctly as direct kwargs
  - `upload_logo` (line ~998) — same

**`test_patch_personality_audit.py`:**
- Docstring updated to cover T-2 + T-2.bis
- § 4 added: `TestEmitTelemetryForwardsTenantId` (4 tests, no DB required)

### Validators Run

| Validator | Command | Result |
|---|---|---|
| `be_patch_personality` (§ 4 telemetry) | `pytest tests/modules/vitalia/brand_studio/test_patch_personality_audit.py -v -k TestEmitTelemetry` | **4 PASSED** |
| Full brand_studio suite | `pytest tests/modules/vitalia/brand_studio/ -v` | **124 PASSED, 73 SKIPPED** |
| `be_lint` | `ruff check src/modules/vitalia/brand_studio/ tests/modules/vitalia/brand_studio/ --no-cache` | **CLEAN** |
| `be_lint` (format) | `ruff format --check ...marca_service.py ...test_patch_personality_audit.py` | **CLEAN** |
| `be_arch_fitness` | `pytest tests/architecture/ -q` | **330 PASSED** |
