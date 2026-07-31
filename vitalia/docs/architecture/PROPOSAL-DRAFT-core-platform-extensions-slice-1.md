---
status: draft
target_skill: /pm-vitalia
target_proposal_path: docs/promotion-protocol/proposals/2026-05-20-core-platform-extensions-slice-1.md
created_at: 2026-05-20
created_by: /pm-vitalia (ratified Chris 2026-05-20 sesión replan Slice 1)
type: promotion-proposal-draft
purpose: |
  Draft de proposal combinado para /pm-vitalia levantar lift cementado en docs/promotion-protocol/proposals/.
  Verify-first findings cementados (cron@idempotent ya está en core — sólo lift envelope).
---

# DRAFT — Core platform extensions Slice 1 (combinado)

> **Target:** `core/luana-core-platform` 0.2.0 → 0.3.0
> **Origen:** ratified Chris 2026-05-20 (sesión replan Slice 1 vitalia). Un proposal combinado en lugar de dos separados.
> **Estado:** DRAFT — `/pm-vitalia` produce este insumo. `/pm-vitalia` levanta proposal real en `docs/promotion-protocol/proposals/`, ratifica, y migra.

## § 1 — Findings verify-first (CRÍTICO)

Pre-condición Chris 2026-05-20: "antes de promover revisa si ya está promovido en core".

### Finding A — `@idempotent` decorator (idempotency check) — YA EN CORE ✅

Path canónico: `core/luana-core-idempotency/src/luana_core_idempotency/application/decorator.py`

Vitalia `_shared/workers/base.py::idempotent_cron` **ya consume `luana_core_idempotency.application.decorator.idempotent`** internamente. NO se duplica.

Lo que el wrapper vitalia añade sobre `@idempotent`:

1. `cron_span` (OTel tracing) — `vitalia/_shared/observability/cron_spans.py`
2. structlog audit on completion
3. Sentry capture on exception (best-effort)
4. Pattern de uso opinionado: `@idempotent_cron("vitalia.cron.followup_24h")` (1-arg name) vs `@idempotent(namespace=..., key_fn=..., ttl=...)` (3-arg verbose).

→ **Conclusión:** lift candidate es el ENVELOPE (los 4 ítems arriba), NO el idempotency check. Reframe de la proposal name: `cron_envelope` (no `idempotent_cron`).

### Finding B — `PhiRepositoryBase` (dual-filter tenant + scope) — NO EXISTE EN CORE ✅ genuine lift

Path actual: `vitalia/backend/src/modules/vitalia/_shared/repositories/phi_repository.py`

Grep `core/luana-core-*/src` retorna vacío para:

- `PhiRepositoryBase`
- `CompoundScopeRepositoryBase`
- `tenant_id.*clinic_id` / `clinic_id.*tenant_id`

→ **Conclusión:** genuine lift candidate. Reframe nombre para abrir a brands no-salud: `CompoundScopeRepositoryBase` (axis names: `tenant_id` + `scope_id`, dejando que brand consumer dé semántica `clinic_id` / `studio_id` / `store_id`).

## § 2 — Proposal: lift combinado `core-platform-extensions-slice-1`

### 2.1 — `cron_envelope` → `core/luana-core-platform/workers/cron_envelope.py`

Wrap `luana_core_idempotency.application.decorator.idempotent` con:

- OTel tracing span (graceful degradation cuando OTel no instalado)
- structlog audit on completion
- Sentry capture on exception (graceful degradation cuando sentry_sdk no instalado)
- API opinionada `@cron_envelope("namespace.dot.path", ttl=600)`

Usage:

```python
# Antes (vitalia/_shared/workers/base.py local)
from src.modules.vitalia._shared.workers.base import idempotent_cron

@idempotent_cron("vitalia.cron.followup_24h")
async def followup_24h(ctx: dict) -> None: ...

# Después (core)
from luana_core_platform.workers.cron_envelope import cron_envelope

@cron_envelope("vitalia.cron.followup_24h")
async def followup_24h(ctx: dict) -> None: ...
```

### 2.2 — `CompoundScopeRepositoryBase` → `core/luana-core-platform/repositories/compound_scope_repository.py`

Abstract base class para repos con dual-filter `tenant_id + scope_id`:

```python
class CompoundScopeRepositoryBase(Generic[ModelT, IdT]):
    """Repo base con dual-scope filter (tenant_id + scope_id) para multitenant compound isolation.

    Brand-specific axis name (clinic_id, studio_id, store_id) se especifica via
    config explicit en constructor — engine NO hardcodea axis semántico.
    """
    def __init__(self, *, session: AsyncSession, scope_field: str = "scope_id"):
        self._session = session
        self._scope_field = scope_field  # vitalia → "clinic_id" · fitflow → "studio_id" · retailly → "store_id"

    async def get_by_id(self, *, id: IdT, tenant_id: UUID, scope_id: UUID) -> ModelT | None:
        scope_attr = getattr(self.MODEL, self._scope_field)
        stmt = select(self.MODEL).where(
            self.MODEL.id == id,
            self.MODEL.tenant_id == tenant_id,
            scope_attr == scope_id,
            self.MODEL.deleted_at.is_(None),
        )
        ...
```

### 2.3 — Side effects en vitalia post lift

- `vitalia/_shared/workers/base.py` → DELETE (replaced por engine import)
- `vitalia/_shared/repositories/phi_repository.py` → DELETE (replaced por engine import)
- 11 callers vitalia (los grep'd) actualizan imports:
  - `from src.modules.vitalia._shared.workers.base import idempotent_cron` → `from luana_core_platform.workers.cron_envelope import cron_envelope`
  - `from src.modules.vitalia._shared.repositories.phi_repository import PhiRepositoryBase` → `from luana_core_platform.repositories.compound_scope_repository import CompoundScopeRepositoryBase`
  - Constructor `PhiRepositoryBase()` → `CompoundScopeRepositoryBase(session=..., scope_field="clinic_id")`

## § 3 — Versionado SemVer

- `core/luana-core-platform` 0.2.0 → **0.3.0** (MINOR — additions, no breaks)
- Vitalia consumer update minor: `vitalia/backend@0.1.0` → `0.1.1` (internal package version)
- Cross-brand impact: ninguno hoy (vitalia es el primer consumer real de ambos patterns). fitflow/retailly futuros heredan al opt-in.

## § 4 — Tests cross-engine

Engine new package tests:
- `core/luana-core-platform/tests/workers/test_cron_envelope.py` (idempotent + OTel + audit + sentry graceful degrad)
- `core/luana-core-platform/tests/repositories/test_compound_scope_repository.py` (dual filter + scope_field configurable)

Vitalia consumer tests:
- Re-correr suites cron jobs (`vitalia/backend/tests/agentic/lucas/cron/*`) post import change → GREEN cap
- Re-correr suites repos (`vitalia/backend/tests/modules/vitalia/crm/*` + `compliance/*` + `agentic/lucas/*` + `sales_agent/*`) post import change → GREEN cap

## § 5 — Origen + ratification

- Origen: 2 learnings vitalia `2026-05-18-phi-repository-base.md` (promotable: candidate) + `2026-05-18-idempotent-cron-pattern.md` (promotable: candidate)
- Chris ratificó verify-first 2026-05-20: idempotent ya en core, lift solo envelope. Combinado en 1 proposal.
- Bloqueo: Ola 1 Slice 1 vitalia NO arranca hasta este proposal state=migrated.

## § 6 — Next steps `/pm-vitalia`

1. Leer este draft.
2. Crear proposal real en `docs/promotion-protocol/proposals/2026-05-20-core-platform-extensions-slice-1.md` con frontmatter `state: draft`.
3. Implementar engine new module `core/luana-core-platform/{workers,repositories}/...` + tests.
4. Bump version + CHANGELOG.
5. Update proposal state: draft → accepted → migrated.
6. Update vitalia learnings frontmatter: `promotable: yes` + `proposal_link:` field.
7. `/pm-vitalia` ping `/pm-vitalia` cuando migrated → Ola 1 inicia /architect refresh.
