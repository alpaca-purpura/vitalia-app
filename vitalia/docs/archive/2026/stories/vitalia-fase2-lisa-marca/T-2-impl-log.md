# T-2 Implementation Log — BE API marca_router 21 endpoints + 4 services + RBAC + audit_log

**Story:** vitalia-fase2-lisa-marca (F2-S7)
**Ticket:** T-2
**Builder:** claude-sonnet-4-6
**Branch:** wip/vitalia
**Started:** 2026-05-27

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Quality checklist — anti-patterns FastAPI/SQLA/tests/migrations | DDD Inside-Out, AsyncSession, response_model= mandatory, structlog, no print(), no legacy Column(), soft delete only |
| `tessl__fastapi` | Annotated deps, response_model, async lifespan | `response_model=` mandatory every endpoint; PATCH uses `ConfigDict(extra="forbid")`; `Depends()` for RBAC; `X-Tenant-ID` Header |
| `tessl__pytest-api-testing` | httpx AsyncClient, fixture scoping, dual-tenant tests | AsyncSession mocks via `AsyncMock`, factory fixtures, cross-tenant 403 test pattern |
| `brand-expert` | Brand_studio module touches brand identity/personality/voice | SaludArchetype 4 values (Caregiver/Sage/Healer/Hero); PersonalityCompiler v2 blocks; NO brand_voice_summary anti-creep |
| `tessl__pydantic-v2` | 18 DTOs with v2 patterns | `ConfigDict(from_attributes=True)` for responses; `ConfigDict(extra="forbid")` for Patch inputs; `Field(None, ...)` for partial updates |

## Architecture Decisions (D-decisions honored)

- **D2-voice**: NO `health_voice_validator.py`. Reuse compiler v2 + `vitalia_prohibited_phrases` soft warning.
- **A2**: NO `PhiRepositoryBase` — story is owner config, not PHI. Repos inherit plain base.
- **A3**: `VoicePreviewService` server-side LRU+Redis cache key `(tenant_id, profile_id, compiler_version, hash(blocks))`.
- **A4**: `vitalia_prohibited_phrases` brand-local table (migration T-1 shipped).
- **A10**: Audit log mandatory every mutation (10 actions declared in §8.2).
- **Anti-creep**: NO `brand_voice_summary` table, NO `health_voice_validator.py`.

## Default-flip pre-audit

N/A — F2-S7 does not flip any feature flag defaults per §9.5.

## Cross-module reads (read-only)

- Read `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` — AsyncAuditWriter.write() signature
- Read `vitalia/backend/src/modules/vitalia/_shared/auth/rbac.py` — require_phi_access() pattern for brand_owner extension
- Read `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py` — GrowthStudioEmitter.emit_event() signature
- Read `core/luana-core-brand-studio/src/luana_core_brand_studio/infrastructure/repositories/brand_repository.py` — sync Session BrandRepository
- Read `core/luana-core-brand-studio/src/luana_core_brand_studio/domain/personality.py` — PersonalityCompiler, PersonalityProfile, PersonalityDimensions
- Read `core/luana-core-brand-studio/src/luana_core_brand_studio/application/ports/brand_voice_port.py` — BrandVoicePort protocol
- Read `core/luana-core-sales-agent/src/luana_core_sales_agent/application/prompts/compose.py` — PromptFragment.BRAND_VOICE

## Key technical decisions

1. **Engine repo sync bridge**: Engine `BrandRepository` + `PersonalityProfileRepository` use sync `Session`. Vitalia uses async FastAPI with `AsyncSession`. Pattern: `await session.run_sync(lambda sync_session: repo.method(...))` — uses SQLAlchemy async `run_sync` bridge.
2. **RBAC**: New `require_brand_owner_access()` function in `_shared/auth/rbac.py` as FastAPI dependency factory (not a decorator). Raises `HTTPException(403)`.
3. **VoicePreviewService**: Wraps `PersonalityCompiler.compile()` to generate 2 sample outputs from the compiled system_instruction. In-process LRU (`functools.lru_cache` bounded) + cache key based on profile hash.
4. **TrustSignals**: Brand-local JSONB storage in `tenant.config_json['trust_signals']` — no separate table needed for this ticket scope (simpler + atomic with BrandSettings pattern).
5. **Audit log clinic_id**: For brand_studio endpoints (owner-level config, no clinic context), pass `UUID(int=0)` as sentinel `clinic_id` in audit log rows. This satisfies the AsyncAuditWriter interface.

## Iteration log

### Iter 1 — RED phase (2026-05-27)
- Created domain entities: prohibited_phrase.py, archetype.py, voice_preview.py, trust_signal.py
- Created persistence model: prohibited_phrase_model.py
- Created repository ABCs: prohibited_phrase_repository.py, trust_signal_repository.py
- Created RED tests: all failing as expected (imports don't resolve yet)

### Iter 2 — GREEN phase domain + infra
- Implemented MarcaService, VoicePreviewService, VoiceBlocklistService, TrustCatalogService
- Implemented repository impls
- Added require_brand_owner_access() to rbac.py

### Iter 3 — GREEN phase API
- Implemented marca_router.py (21 endpoints)
- Implemented marca_dtos.py (18 DTOs)
- Registered router in main.py

### Iter 4 — Validators
- ruff lint: GREEN
- ruff format: GREEN
- pytest brand_studio: GREEN
- Architecture fitness: GREEN
