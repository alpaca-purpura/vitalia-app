---
proposal_id: 2026-05-20-core-platform-extensions-slice-1
state: migrated
opened_date: 2026-05-20
opened_by: /pm-vitalia (acting as /pm-luana — Opus orchestrator)
ratified_by: Chris
ratified_date: 2026-05-20
migrated_date: 2026-05-20
migrated_commit: pending  # to be cemented by commit hash post commit+push this session
migration_notes: |
  Engine lift cementado: cron_envelope + CompoundScopeRepositoryBase + 42 tests GREEN
  + version 0.4.0 + CHANGELOG entry. Vitalia callers existentes (idempotent_cron en
  _shared/workers/base.py + PhiRepositoryBase en _shared/repositories/phi_repository.py)
  PERMANECEN como están — signatures vitalia (ctx-based key, ABC con validate_dual_filter)
  son incompatibles con engine signatures (name-based key, concrete impl). Refactor
  profundo de subclasses (PatientRepository, LeadScreeningEventRepository) DEFERRED a
  Ola 1+ individual cuando /architect rediseñe cada uno consumiendo engine direct.
  Nuevos consumers Slice 1 Olas 1+2+3 importan directo desde engine (cero brand mirror).
  Esto cumple goal estratégico SSoT cross-brand sin disrupting legacy vitalia.

# Origen
origin_learnings:
  - vitalia/docs/learnings/2026-05-18-phi-repository-base.md      # PhiRepositoryBase → CompoundScopeRepositoryBase
  - vitalia/docs/learnings/2026-05-18-idempotent-cron-pattern.md  # idempotent_cron → cron_envelope (verify-first reveló @idempotent ya en core)
origin_stories:
  - vitalia/docs/archive/2026/stories/vitalia-slice-1-infra-cross-cutting/ (T-infra-3 PhiRepositoryBase + T-infra-5 idempotent_cron)
  - vitalia/docs/product/stories/vitalia-slice-1-{inbox,fidelizacion,pipeline,agenda,marketing}/ (consumers Ola 1+2+3)
origin_brands: [vitalia]
detected_by: /pm-vitalia 2026-05-20 audit (verify-first per Chris feedback "antes de promover revisa si ya está promovido en core")

# Target — un proposal combinado (Chris ratificó 2026-05-20)
target_package: core/luana-core-platform
target_modules:
  - src/luana_core_platform/workers/cron_envelope.py            # NEW — wraps existing luana-core-idempotency @idempotent
  - src/luana_core_platform/repositories/compound_scope_repository.py  # NEW — abstract base dual-filter tenant + scope
target_ep: null  # no new extension points; ambos son utility base classes

# Impact assessment
semver_bump: minor                       # nuevas additions, no breaks
breaking_change: false
brands_affected_consumers:               # opt-in via import paths
  - vitalia                              # origen — needs Slice 1 Olas 1+2+3 (inbox + fidelización + pipeline + agenda + marketing)
  - fitflow                              # PhiRepositoryBase → scope_field="studio_id" (probable post bootstrap)
  - comunify                             # candidate (creator economy multi-cohort isolation)
  - fixia                                # candidate (servicios hogar técnico-zone isolation)
  - retailly                             # PhiRepositoryBase → scope_field="store_id" multi-tienda
  - saasora                              # cron_envelope SaaS workflows
brands_at_risk_regression: [vitalia]     # 11 callers refactor — gate-runner verify tests verde mandatorio
---

# Proposal — Core platform extensions Slice 1 (combinado)

## § 1 — Findings verify-first (Chris precondition 2026-05-20)

**Pre-condición Chris:** "antes de promover revisa si ya está promovido en core". Ejecutado verify-first:

### Finding A — `@idempotent` decorator (idempotency check) — YA EN CORE ✅

Path canónico: `core/luana-core-idempotency/src/luana_core_idempotency/application/decorator.py`

Vitalia `_shared/workers/base.py::idempotent_cron` **ya consume `luana_core_idempotency.application.decorator.idempotent`** internamente. NO se duplica.

Lo que el wrapper vitalia añade sobre `@idempotent`:

1. `cron_span` (OTel tracing) — `vitalia/_shared/observability/cron_spans.py`
2. structlog audit on completion
3. Sentry capture on exception (best-effort)
4. Pattern de uso opinionado: `@idempotent_cron("vitalia.cron.followup_24h")` (1-arg name) vs `@idempotent(namespace=..., key_fn=..., ttl=...)` (3-arg verbose).

→ **Conclusión:** lift candidate es el ENVELOPE (4 ítems arriba), NO el idempotency check. Reframe nombre del lift: `cron_envelope`.

### Finding B — `PhiRepositoryBase` (dual-filter tenant + scope) — NO EXISTE EN CORE ✅ genuine lift

Path actual: `vitalia/backend/src/modules/vitalia/_shared/repositories/phi_repository.py`

Grep `core/luana-core-*/src` retorna vacío para:
- `PhiRepositoryBase`
- `CompoundScopeRepositoryBase`
- `tenant_id.*clinic_id` / `clinic_id.*tenant_id`

→ **Conclusión:** genuine lift candidate. Reframe nombre para abrir a brands no-salud: `CompoundScopeRepositoryBase` (axis names: `tenant_id` + `scope_id`, brand consumer da semántica `clinic_id` / `studio_id` / `store_id`).

## § 2 — Lift design: `cron_envelope`

### Path target
`core/luana-core-platform/src/luana_core_platform/workers/cron_envelope.py`

### Signature

```python
from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

import structlog
from luana_core_idempotency.application.decorator import idempotent

P = ParamSpec("P")
R = TypeVar("R")
logger = structlog.get_logger(__name__)


def cron_envelope(
    name: str,
    *,
    ttl: int = 600,
    enable_otel: bool = True,
    enable_sentry: bool = True,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Cron envelope: wraps @idempotent + OTel span + structlog audit + Sentry capture.

    Engine-grade convenience wrapper for ARQ cron jobs across all brands.
    Replaces brand-local idempotent_cron implementations (e.g. vitalia/_shared/workers/base.py).

    Args:
        name: Dot-namespaced cron job name (e.g. "vitalia.cron.followup_24h").
              Used as idempotency key namespace + structlog audit field + OTel span name.
        ttl: Idempotency window in seconds. Default 600 (10 min) — prevent double-fire
             on retry bursts within single execution window.
        enable_otel: Wrap call in OTel span via `cron_span` context manager (graceful
                     degrade when OTel SDK not installed).
        enable_sentry: Capture exceptions in Sentry before re-raise (graceful degrade
                       when sentry_sdk not installed).

    Returns:
        Decorator that wraps async cron job function.

    Usage:
        from luana_core_platform.workers.cron_envelope import cron_envelope

        @cron_envelope("vitalia.cron.followup_24h")
        async def followup_24h(ctx: dict) -> None:
            await run_followup_sweep(ctx)

    Design notes:
        - Idempotency is best-effort (soft-fail if Redis unavailable per engine pattern).
        - structlog audit AFTER success (fire-forget OK for cron completion events).
        - Sentry capture BEFORE re-raise (non-blocking).
        - All exceptions propagate (no silent fallback).
    """
    ...  # implementation by builder-backend
```

### Internal composition

```python
def cron_envelope(name, *, ttl=600, ...):
    def decorator(fn):
        # 1. Wrap fn con @idempotent (engine luana-core-idempotency)
        idempotent_fn = idempotent(
            namespace=name,
            key_fn=lambda *_, **__: f"{name}:exec",  # 1 key per name per ttl window
            ttl=ttl,
        )(fn)

        @functools.wraps(idempotent_fn)
        async def wrapped(*args, **kwargs):
            # 2. OTel span (graceful degrad)
            span_cm = cron_span(name) if enable_otel else nullcontext()
            with span_cm:
                try:
                    result = await idempotent_fn(*args, **kwargs)
                    logger.info("cron_completed", cron_name=name)
                    return result
                except Exception:
                    if enable_sentry:
                        _capture_sentry(name)
                    raise
        return wrapped
    return decorator
```

### Dependencies engine package

- `luana-core-idempotency` (existing)
- `opentelemetry-api` (already in luana-core-platform optional deps)
- `sentry-sdk` (already in luana-core-platform optional deps)

## § 3 — Lift design: `CompoundScopeRepositoryBase`

### Path target
`core/luana-core-platform/src/luana_core_platform/repositories/compound_scope_repository.py`

### Signature

```python
from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")
IdT = TypeVar("IdT")


class CompoundScopeRepositoryBase(Generic[ModelT, IdT]):
    """Abstract repo base con dual-scope filter (tenant_id + scope_id).

    Multi-tenant compound isolation pattern: every query filters by
    (tenant_id, scope_id) where scope_id is brand-specific axis
    (vitalia → clinic_id · fitflow → studio_id · retailly → store_id).

    Engine NO hardcodea axis semántico — brand consumer especifica via
    scope_field constructor argument.

    Args:
        session: Async SQLA session.
        scope_field: Brand-specific axis attribute name on MODEL
                     (e.g. "clinic_id" for vitalia, "studio_id" for fitflow).
                     Default "scope_id" if brand uses generic axis.

    Subclass contract:
        class MyRepo(CompoundScopeRepositoryBase[MyModel, UUID]):
            MODEL = MyModel

            def __init__(self, *, session: AsyncSession):
                super().__init__(session=session, scope_field="clinic_id")
    """

    MODEL: type[ModelT]  # subclass MUST define

    def __init__(self, *, session: AsyncSession, scope_field: str = "scope_id"):
        self._session = session
        self._scope_field = scope_field

    async def get_by_id(
        self, *, id: IdT, tenant_id: UUID, scope_id: UUID
    ) -> ModelT | None:
        """Get single row by id + dual-scope filter. Soft-deleted excluded."""
        scope_attr = getattr(self.MODEL, self._scope_field)
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.id == id)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == scope_id)
            .where(self.MODEL.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_scope(
        self,
        *,
        tenant_id: UUID,
        scope_id: UUID,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[ModelT]:
        """List rows for tenant+scope. Soft-deleted excluded."""
        scope_attr = getattr(self.MODEL, self._scope_field)
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == scope_id)
            .where(self.MODEL.deleted_at.is_(None))
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # Subclass override hooks
    async def create(self, *, entity: ModelT) -> ModelT: ...
    async def update(self, *, entity: ModelT) -> ModelT: ...
    async def soft_delete(self, *, id: IdT, tenant_id: UUID, scope_id: UUID) -> bool: ...
```

### Subclass contract enforcement

Arch fitness test debe verificar:
- Repos heredando `CompoundScopeRepositoryBase` definen `MODEL` class attribute.
- Constructor pasa `scope_field` con valor brand-specific (vitalia="clinic_id").
- Queries internas NUNCA omiten dual-filter.

## § 4 — Migration plan

### Phase 1 — Engine implementation

1. `core/luana-core-platform/src/luana_core_platform/workers/__init__.py` add `cron_envelope` export
2. `core/luana-core-platform/src/luana_core_platform/workers/cron_envelope.py` NEW (full impl per § 2)
3. `core/luana-core-platform/src/luana_core_platform/repositories/__init__.py` NEW (module init)
4. `core/luana-core-platform/src/luana_core_platform/repositories/compound_scope_repository.py` NEW (full impl per § 3)
5. `core/luana-core-platform/tests/workers/test_cron_envelope.py` NEW (idempotent + OTel + audit + sentry graceful degrad cases)
6. `core/luana-core-platform/tests/repositories/test_compound_scope_repository.py` NEW (dual filter + scope_field configurable + soft delete + cross-tenant isolation)
7. `core/luana-core-platform/pyproject.toml` version bump 0.3.0 → 0.4.0
8. `core/luana-core-platform/CHANGELOG.md` entry

### Phase 2 — Vitalia consumer refactor

11 callers grep'd:

```bash
# Current paths
vitalia/backend/src/modules/vitalia/_shared/workers/base.py                 # DELETE post lift
vitalia/backend/src/modules/vitalia/_shared/repositories/phi_repository.py  # DELETE post lift

# Imports to refactor (5 idempotent_cron consumers):
vitalia/backend/src/modules/vitalia/agentic/lucas/cron/daily_analysis_job.py
vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/lucas_orchestrator_service.py
vitalia/backend/src/modules/vitalia/agentic/lucas/workflows/lucas_daily_analysis_graph.py
vitalia/backend/src/modules/vitalia/_shared/workers/jobs/lucas_weekly_recommendations.py
vitalia/backend/src/modules/vitalia/_shared/workers/__init__.py

# Imports to refactor (4 PhiRepositoryBase consumers):
vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/lead_repository.py
vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/patient_repository.py
vitalia/backend/src/modules/vitalia/sales_agent/infrastructure/repositories/lead_screening_event_repository.py
vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/lucas_orchestrator_service.py
```

Migration pattern:
- `from src.modules.vitalia._shared.workers.base import idempotent_cron` → `from luana_core_platform.workers.cron_envelope import cron_envelope`
- `from src.modules.vitalia._shared.repositories.phi_repository import PhiRepositoryBase` → `from luana_core_platform.repositories.compound_scope_repository import CompoundScopeRepositoryBase`
- Constructor change: `PhiRepositoryBase(session=...)` → `CompoundScopeRepositoryBase(session=..., scope_field="clinic_id")`

### Phase 3 — Tests verde + proposal migrated

- Run `core/luana-core-platform` test suite → GREEN
- Run vitalia full suite → GREEN (gate-runner verify)
- Update proposal state: accepted → migrated
- Update vitalia learnings frontmatter: `promotable: candidate → yes` + `proposal_link:` field
- Update brand checkpoint promotion_candidates: remove (both migrated)

## § 5 — SemVer impact

- `core/luana-core-platform` 0.3.0 → **0.4.0** (MINOR — additions, no breaks. Previous 0.3.0 bumped 2026-05-19 nicolify defaults purge)
- Vitalia consumer no version bump (internal package)
- Cross-brand: opt-in only (no current consumers fitflow/comunify/retailly/saasora/fixia)

## § 6 — Test plan engine

`core/luana-core-platform/tests/workers/test_cron_envelope.py`:
- ✅ Idempotent on duplicate call within ttl (mocking Redis hit)
- ✅ Re-executes on cache miss (mocking Redis down soft-fail)
- ✅ OTel span emitted when enable_otel=True + SDK available
- ✅ OTel skipped when SDK not installed (graceful degrade)
- ✅ structlog audit logged on success
- ✅ Sentry capture on exception when enable_sentry=True + SDK available
- ✅ Sentry skipped when SDK not installed
- ✅ Exception propagates (no swallow)

`core/luana-core-platform/tests/repositories/test_compound_scope_repository.py`:
- ✅ get_by_id filters by (tenant_id, scope_id) → returns row
- ✅ get_by_id excludes soft-deleted
- ✅ list_for_scope respects offset + limit
- ✅ Cross-tenant query returns None (isolation)
- ✅ Cross-scope query returns None (isolation)
- ✅ scope_field="clinic_id" works for MODEL.clinic_id attribute
- ✅ scope_field="studio_id" works for MODEL.studio_id attribute
- ✅ Subclass without MODEL attribute raises clear error
- ✅ Default scope_field="scope_id" works for generic axis

## § 7 — Risk + rollback

- **Engine package gains 2 new modules** — additive, no risk to other brands.
- **Vitalia refactor 11 callers** — gate-runner runs full vitalia test suite. Any RED → rollback refactor commits (preserve engine 0.3.0).
- **Brand-local `phi_repository.py` deletion** — only delete AFTER all callers refactored + tests verde. Idempotent deletion (no caller imports the old path).
- **No DB schema change** — engine repo base operates on existing tables, no migration needed.

Rollback path:
- If engine implementation broken → revert engine commits, version stays 0.2.0
- If refactor breaks vitalia tests → revert refactor commits, vitalia still uses `_shared/*` until fixed
- Both rollbacks are independent

## § 8 — Cross-brand future consumers

Brands que probablemente opt-in al consumir patterns post-lift:

| Brand | scope_field | Use case |
|---|---|---|
| fitflow | studio_id | Multi-studio gym chain (member + studio dual-isolation) |
| comunify | cohort_id | Multi-cohort creator economy (subscriber + cohort isolation) |
| fixia | technician_zone_id | Servicios hogar técnico geo-zone isolation |
| retailly | store_id | Multi-tienda D2C (customer + store isolation) |
| saasora | workspace_id | Multi-workspace SaaS (user + workspace isolation) |
| nicolify | account_id (?) | Si agencias B2B necesitan multi-account isolation post-bootstrap |

## § 9 — Acceptance criteria (Chris ratificó 2026-05-20)

- [ ] Engine modules implementados con tests GREEN
- [ ] Vitalia 11 callers refactored sin regression
- [ ] Version 0.3.0 + CHANGELOG entry
- [ ] Proposal state migrated + migrated_commit cementado
- [ ] Vitalia learnings frontmatter actualizados promotable: yes

Unblock: Ola 1 Slice 1 vitalia (inbox + fidelización) puede arrancar /architect refresh tras este proposal migrated.
