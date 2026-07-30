# T-onboarding-1 — IMPL-LOG

## Story
`vitalia-slice-1-onboarding-wizard` · Ticket: T-onboarding-1

## Summary
Replaced AsyncMock placeholder DI factories in `wizard_onboarding_routes.py` with real SQLA 2.0 repository implementations. Implemented Inside-Out DDD layers: domain interfaces → ORM models → infrastructure implementations → DI wire-up.

---

## § Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `backend-expert` | Primary skill per role — loads runtime-quality-checklist anti-patterns (FastAPI Annotated dep, override fixture, datetime query, SQLA legacy Column, tenant isolation pattern) | Confirmed SQLA 2.0 `select().where()` pattern; no `session.query()`, no `Column()`, no `datetime.utcnow()`; all queries filter `tenant_id` including bridge `get_by_id` |
| `tessl__fastapi` | Annotated deps + response_model + async DI for real session injection | Used `Annotated[AsyncSession, Depends(get_async_session)]` pattern for all repo factories; async generator session factory in `src/db.py` |
| `tessl__pytest-api-testing` | AsyncMock-based unit tests without real DB — fixture scoping, factory fixtures | Used `AsyncMock(spec=AsyncSession)` + `MagicMock` for scalar results; all 27 tests non-integration (no `@pytest.mark.integration`) |

---

## § Default-flip pre-audit (Step 0.5)
No config flags were modified. Not applicable.

---

## § Implementation notes

### Files created
1. `vitalia/backend/src/db.py` — `get_async_session` async generator; reads `DATABASE_URL` env (canonical) or fallback `POSTGRES_*` vars
2. `vitalia/backend/src/modules/vitalia/copilot/domain/entities/brand_studio_draft.py` — pure Python dataclass (no framework imports)
3. `vitalia/backend/src/modules/vitalia/copilot/domain/repositories/__init__.py` — package init
4. `vitalia/backend/src/modules/vitalia/copilot/domain/repositories/onboarding_progress_repository.py` — ABC with `create`, `get_by_tenant_user`, `update_step`, `mark_completed` + bridge `save`/`get_by_id` for `OnboardingDraftService` compat
5. `vitalia/backend/src/modules/vitalia/copilot/domain/repositories/brand_studio_draft_repository.py` — ABC with `create`, `get_by_id_tenant`, `append_payload_patch`, `mark_committed`
6. `vitalia/backend/src/modules/vitalia/copilot/persistence/models/onboarding_progress_model.py` — SQLA 2.0 ORM backing `vitalia_onboarding_progress` (migration 011 already applied)
7. `vitalia/backend/src/modules/vitalia/copilot/persistence/models/brand_studio_draft_model.py` — SQLA 2.0 ORM backing `vitalia_brand_studio_drafts` (migration 012 already applied)
8. `vitalia/backend/src/modules/vitalia/copilot/infrastructure/repositories/onboarding_progress_repository.py` — `SqlAlchemyOnboardingProgressRepository` implementing the ABC; all queries filter `tenant_id`; bridge methods `save()` and `get_by_id()` added to serve existing `OnboardingDraftService`
9. `vitalia/backend/src/modules/vitalia/copilot/infrastructure/repositories/brand_studio_draft_repository.py` — `SqlAlchemyBrandStudioDraftRepository` implementing the ABC
10. `vitalia/backend/tests/modules/vitalia/copilot/__init__.py` + subdirs `__init__.py` × 2
11. `vitalia/backend/tests/modules/vitalia/copilot/infrastructure/repositories/test_onboarding_progress_repository.py` — 14 unit tests
12. `vitalia/backend/tests/modules/vitalia/copilot/infrastructure/repositories/test_brand_studio_draft_repository.py` — 13 unit tests

### Files modified
- `vitalia/backend/src/modules/vitalia/copilot/api/routes/wizard_onboarding_routes.py` — replaced AsyncMock factories with real `Depends(get_async_session)` DI; `get_onboarding_draft_service` / `get_extract_service` / `get_complete_service` now use `SqlAlchemyOnboardingProgressRepository`; `get_simulate_service` still stubbed (no DB for simulation)

### Key design decisions
- **Bridge methods on progress repo**: `OnboardingDraftService` (shipped, not modified) calls `draft_repo.save(draft)` and `draft_repo.get_by_id(id, tenant_id=...)`. Rather than modifying the shipped service, `SqlAlchemyOnboardingProgressRepository` adds bridge methods to satisfy the service interface.
- **`luana_core_platform.domain.base_entity.Base`**: mini-arch spec referenced `VitaliaBase` which does not exist post-reorg. Used correct Base from `luana_core_platform` per existing ORM model pattern in `copilot_llm_call.py`.
- **HIPAA-lite**: wizard tables (onboarding config + voice samples) are NOT PHI — single `tenant_id` filter only per `.claude/rules/hipaa-lite.md` (no `clinic_id` dual filter required).
- **Slot state in JSONB**: `_model_to_draft()` reconstructs `WizardSlot` dicts from JSONB; `slots_confirmed` → `slots_required`; `slots_pending` → `slots_optional`.
- **No new migration**: tables 011 + 012 already applied; no DDL changes needed.

---

## § Cross-module reads
- Read `vitalia/backend/src/modules/vitalia/copilot/api/routes/wizard_onboarding_routes.py` (read-only analysis before modification — owned by builder-agentic; modification scope: AsyncMock DI factories only, no domain/application/tool logic touched)
- Read existing ORM model `copilot/persistence/models/copilot_llm_call.py` for `Base` import pattern (read-only)

---

## § Quality gates

| Gate | Result |
|---|---|
| `ruff check` | 0 errors |
| `ruff format --check` | 23 files already formatted |
| Architecture fitness (`tests/architecture/`) | 245/245 PASS |
| Module unit tests (`tests/modules/vitalia/copilot/`) | 27/27 PASS |
| Tenant isolation | All queries filter `tenant_id`; bridge `get_by_id` also filters `tenant_id` |
| Soft delete | `status != 'abandoned'` filter in `get_by_tenant_user` (tables use status-based lifecycle, no `deleted_at`) |
| SQLA 2.0 compliance | `select(Model).where(...)`, `mapped_column`, `Mapped[type]`, `DateTime(timezone=True)`, `AsyncSession` |
