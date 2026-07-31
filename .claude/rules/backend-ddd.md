---
globs: "core/luana-core-*/src/**/*.py,**/backend/src/**/*.py"
description: Backend DDD (engine + per-brand)
---

# Backend DDD

## Layers (Inside-Out)
`domain` → `infrastructure` → `application` → `api`. Domain pure (no framework). Infrastructure implementa interfaces domain. Application = services/use cases. API = FastAPI routes + Pydantic DTOs (thin).

Aplica al engine (`core/luana-core-*/src/luana_core_*/`) y a cada brand (`{brand}/backend/src/modules/{brand}/...`).

## Constraints
- Every query filter `tenant_id` (incluye `get_by_id`).
- Soft deletes only (`deleted_at`).
- SQLA 2.0 `select(Model).where(...)` (no `session.query()`).
- New code `AsyncSession`. Legacy `Session` migrate incrementally.
- `structlog`, no `print`/`logging`.
- Pydantic v2 `model_config = ConfigDict(...)` (no inner `class Config`).

## FastAPI app
`FastAPI(redirect_slashes=False)` mandatory en `{brand}/backend/src/main.py` (default `True` → 307 POST → Next.js drops body). Arch test enforces per brand. NUNCA en `APIRouter` individual.

## Cross-module / cross-brand imports
- Cross-module dentro del mismo brand: default forbidden. Excepción: `copilot` (infra-like). Otros: port/interface en `core/luana-core-platform/src/luana_core_platform/links/` o domain event vía `core/luana-core-events/`.
- Cross-brand import absolutely forbidden — un brand NUNCA importa de otro brand. Compartir via engine package + Extension SDK.

## Extraction orchestrators
Wave-based LLM extraction (brand/offer/buyer_persona/landing) MUST subclass `luana_core_extraction.base_orchestrator.BaseExtractionOrchestrator` (engine package `core/luana-core-extraction/`). Subclass: wave composition + `_merge_and_save` + `run()`. Arch gate `test_extraction_orchestrator_inheritance.py` (corre en cada brand).

## Schema-mirror exception (origen R5 2026-05-05) — resumen

`builder-backend` MAY touch `{brand}/backend/src/modules/{brand}/{copilot,sales_agent}/persistence/models/` SOLO para schema mirror desde engine migration (add/modify `Mapped[]` columns/indexes/FKs matching DDL). NO toca `domain/application/api/observability` del módulo agentic ni cambia runtime/semantic fields. auditor-backend APPROVE sin escalate. **Detalle completo (qué permite/prohíbe + caso origen PI-12 S1 T-1):** `.claude/skills/backend-expert/references/schema-mirror-exception.md`.

## Multibrand awareness (post reorg 2026-05-15)

- Engine packages: `core/luana-core-*/src/luana_core_*/` — DDD interno aplica + contracts Extension SDK pública.
- Brand backends: `{brand}/backend/src/modules/{brand}/...` — DDD interno aplica + opcional registro Extension SDK.
- Lógica compartible/genérica → lift a engine vía flujo `/pm-vitalia` (arch tests como gate).
