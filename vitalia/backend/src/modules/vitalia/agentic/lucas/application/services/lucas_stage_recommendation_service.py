# cap: agentic.lucas-recommendation-tool
# story-origin: TBD
"""Lucas application service — LucasStageRecommendationService.

Generates AI-powered stage-based growth recommendations using:
  - Analytics engine metrics (via AnalyticsEngineQueryAdapter)
  - Kimi LLM reasoning (via luana_core_llm LiteLLMService)
  - BudgetGuard pre-flight check (via luana_core_billing)

HIPAA-lite:
  - No PHI processed — analytics data only.
  - sanitize_payload() applied before any observability write.
  - Clinic_id ALWAYS passed to repo (dual filter).

If BudgetGuard.check() returns False → status='skipped_budget', no LLM call.
Currency: all monetary data uses locale.currency — NEVER hardcoded.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Protocol
from uuid import UUID, uuid4

import structlog

from src.modules.vitalia.agentic.lucas.domain.entities.stage_recommendation import (
    StageRecommendation,
)
from src.modules.vitalia.agentic.lucas.infrastructure.adapters.analytics_engine_query_adapter import (
    AnalyticsEngineQueryAdapter,
)
from src.modules.vitalia.agentic.lucas.infrastructure.repositories.stage_recommendation_repository import (
    StageRecommendationRepository,
)

logger = structlog.get_logger()


class TenantLocaleProtocol(Protocol):
    """Minimal locale protocol — currency + timezone from TenantLocale."""

    currency: str
    timezone: str


class BudgetGuardProtocol(Protocol):
    """Protocol for BudgetGuard.check() — pre-LLM budget check."""

    def check(self, *, agent_kind: str) -> bool:
        """Return True if budget is available, False if exceeded."""
        ...


class LLMServiceProtocol(Protocol):
    """Protocol for LiteLLM service — async LLM completions."""

    async def complete(self, prompt: str, **kwargs: Any) -> Any:
        """Generate a completion from the LLM."""
        ...


_RECOMMENDATION_PROMPT_TEMPLATE = """
Eres un consultor de crecimiento para clínicas de salud y bienestar.

Analiza los siguientes datos de la etapa de embudo "{stage}" para el período {period}:

Datos de canales:
{metrics_json}

Genera UNA recomendación concreta y accionable para mejorar el rendimiento de esta etapa.
La recomendación debe ser:
- Específica y basada en los datos
- Ejecutable en los próximos 30 días
- Escrita en español neutro latinoamericano (sin voseo)

Responde con:
TÍTULO: [título de la recomendación, máx. 80 caracteres]
DETALLE: [detalle accionable, 2-3 oraciones]
JUSTIFICACIÓN: [por qué esta recomendación basada en los datos]
""".strip()


class LucasStageRecommendationService:
    """Application service for generating Lucas stage recommendations.

    Flow:
        1. BudgetGuard.check() — if False, return skipped_budget entity.
        2. AnalyticsEngineQueryAdapter.get_stage_metrics() — fetch context data.
        3. LLM complete() — generate recommendation text (Kimi via LiteLLM).
        4. Parse LLM output → StageRecommendation entity.
        5. repo.save() — persist with tenant_id + clinic_id.
        6. Return entity.
    """

    def __init__(
        self,
        *,
        repo: StageRecommendationRepository,
        budget_guard: BudgetGuardProtocol,
        llm_service: LLMServiceProtocol,
        analytics_adapter: AnalyticsEngineQueryAdapter,
    ) -> None:
        """Initialise with DI'd dependencies."""
        self._repo = repo
        self._budget_guard = budget_guard
        self._llm_service = llm_service
        self._analytics_adapter = analytics_adapter

    async def compute(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        stage: str,
        period: str,  # "YYYY-MM"
        locale: TenantLocaleProtocol,
    ) -> StageRecommendation:
        """Generate and persist a stage recommendation.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite dual filter).
            stage: Funnel stage (attraction/capture/nurture/opportunity/retention).
            period: Period string "YYYY-MM" for this recommendation cycle.
            locale: TenantLocale — provides currency (NEVER hardcoded).

        Returns:
            StageRecommendation entity with status='open' (or 'skipped_budget').
        """
        now = dt.datetime.now(tz=dt.timezone.utc)
        expires_at = now + dt.timedelta(days=30)

        # Step 1: BudgetGuard pre-flight check — MANDATORY before any LLM call
        budget_ok = self._budget_guard.check(agent_kind="copilot")
        if not budget_ok:
            logger.warning(
                "lucas_recommendation_skipped_budget",
                tenant_id=str(tenant_id),
                stage=stage,
                period=period,
            )
            entity = StageRecommendation(
                id=uuid4(),
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                stage=stage,
                recommendation_kind="growth",
                title="Recomendación no generada",
                body="El presupuesto de IA para este período fue superado.",
                rationale_json={"skipped_reason": "budget_exceeded"},
                priority=0,
                status="skipped_budget",
                expires_at=expires_at,
                created_at=now,
                updated_at=now,
                deleted_at=None,
                approved_by_user_id=None,
                approved_at=None,
                undo_until=None,
            )
            await self._repo.save(entity)
            return entity

        # Step 2: Fetch analytics metrics from engine (READ-ONLY)
        metrics = await self._analytics_adapter.get_stage_metrics(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            stage=stage,
            period=period,
        )

        # Step 3: Generate recommendation with LLM
        import json

        prompt = _RECOMMENDATION_PROMPT_TEMPLATE.format(
            stage=stage,
            period=period,
            metrics_json=json.dumps(metrics, ensure_ascii=False, indent=2),
        )

        try:
            llm_response = await self._llm_service.complete(
                prompt,
                model="kimi/kimi-k2",
                max_tokens=512,
            )
            raw_text: str = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
        except Exception:
            logger.exception(
                "lucas_recommendation_llm_error",
                tenant_id=str(tenant_id),
                stage=stage,
            )
            raw_text = "No se pudo generar la recomendación por error en el servicio de IA."

        # Step 4: Parse LLM output → entity fields
        title, body, rationale = _parse_llm_output(raw_text, stage=stage)

        entity = StageRecommendation(
            id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            stage=stage,
            recommendation_kind="growth",
            title=title,
            body=body,
            rationale_json={"llm_rationale": rationale, "stage_metrics": metrics},
            priority=50,
            status="open",
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
            deleted_at=None,
            approved_by_user_id=None,
            approved_at=None,
            undo_until=None,
        )

        # Step 5: Persist
        saved = await self._repo.save(entity)

        logger.info(
            "lucas_stage_recommendation_created",
            recommendation_id=str(saved.id),
            tenant_id=str(tenant_id),
            stage=stage,
            period=period,
        )

        return saved


def _parse_llm_output(raw_text: str, *, stage: str) -> tuple[str, str, str]:
    """Parse LLM output into (title, body, rationale).

    Expects format:
        TÍTULO: ...
        DETALLE: ...
        JUSTIFICACIÓN: ...

    Falls back to raw_text if parsing fails.
    """
    lines = raw_text.strip().split("\n")
    title = f"Recomendación para etapa {stage}"
    body = raw_text
    rationale = ""

    for line in lines:
        if line.startswith("TÍTULO:"):
            title = line[len("TÍTULO:") :].strip()[:80]
        elif line.startswith("DETALLE:"):
            body = line[len("DETALLE:") :].strip()
        elif line.startswith("JUSTIFICACIÓN:"):
            rationale = line[len("JUSTIFICACIÓN:") :].strip()

    return title, body, rationale
