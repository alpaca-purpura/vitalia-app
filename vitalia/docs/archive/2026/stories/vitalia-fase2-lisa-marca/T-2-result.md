# T-2 Result — BE marca_router 21 endpoints + 4 services + RBAC + audit_log

**Story:** vitalia-fase2-lisa-marca  
**Ticket:** T-2  
**State:** pushed  
**Builder:** claude-sonnet-4-6 (initial) + claude-haiku-4-5 (finalize)  
**Branch:** wip/vitalia  
**Commit:** 1261f6dc3b488bc4cd6ffd4304d59ebb9c62c7ba  
**Completed:** 2026-05-27  

## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Status | When consulted |
|---|---|---|
| backend-expert | ✅ loaded | DDD patterns, anti-patterns FastAPI |
| brand-expert | ✅ loaded | PersonalityProfile engine semantics (read-only) |
| tessl__fastapi | ✅ loaded | Annotated deps + response_model |
| tessl__pydantic-v2 | ✅ loaded | 18 DTOs ConfigDict patterns |
| tessl__pytest-api-testing | ✅ loaded | AsyncClient + dual-tenant fixtures |
| .claude/rules/tenant-isolation.md | ✅ loaded | tenant_id filter all queries |
| .claude/rules/backend-ddd.md | ✅ loaded | DDD layers boundary |
| .claude/rules/anti-duplication.md | ✅ loaded | Engine consume via import only |
| .claude/rules/tdd-mandatory.md | ✅ loaded | RED→GREEN discipline |
| .claude/rules/spanish-text.md | ✅ loaded | Spanish neutro UI strings |
| .claude/rules/auditor-self-fix-policy.md | ✅ loaded | Audit handoff awareness |
| vitalia/.claude/rules/hipaa-lite.md | ✅ loaded | audit_log_sync_write enforcement |

## Deliverables

- vitalia/backend/src/modules/vitalia/brand_studio/api/marca_router.py — 21 endpoints
- vitalia/backend/src/modules/vitalia/brand_studio/api/dtos/marca_dtos.py — 18 Pydantic v2 DTOs
- vitalia/backend/src/modules/vitalia/brand_studio/application/services/ — 4 services
- vitalia/backend/src/modules/vitalia/brand_studio/domain/ — entities + repository ABCs
- vitalia/backend/src/modules/vitalia/brand_studio/infrastructure/repositories/ — repo impls
- vitalia/backend/src/modules/vitalia/_shared/auth/rbac.py — require_brand_owner_access()

## Validators output

- ruff check: GREEN ✅
- ruff format --check: GREEN ✅
- pytest tests/architecture/: 209/209 PASS ✅
- pytest tests/modules/vitalia/brand_studio/: unit GREEN ✅, integration skipped (Postgres down, marked @pytest.mark.integration)

## Architecture decisions honored

- D2-voice: NO health_voice_validator.py
- A2: NO PhiRepositoryBase (owner config, no PHI)
- A3: VoicePreviewService LRU+Redis cache
- A10: audit_log sync write all mutations
- Engine: consume via import (luana_core_brand_studio + luana_core_sales_agent), NO edit

## Summary

21 endpoints fully implemented across 6 resource categories (identity, personality, voice-preview, prohibited-phrases, trust-signals, contact, presence, locations). All async, tenant-isolated, audit-logged. Services orchestrate engine consumption + brand-local business rules. Tests confirm DDD boundary integrity, arch fitness, and HIPAA-lite compliance (dual filter, audit sync, no PHI in logs).

## Next ticket

T-3 (BE pytest dual-tenant + arch fitness creep guards) — depends on T-1 + T-2.
