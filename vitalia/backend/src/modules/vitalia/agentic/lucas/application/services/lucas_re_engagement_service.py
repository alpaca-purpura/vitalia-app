# cap: agentic.lucas-daily-analysis
# story-origin: TBD
"""Lucas application service — LucasReEngagementService.

T-10 Slice 1 fidelización agentic. R23 production_code=True (Opus 4.7 exclusive).

Aggregates re_engagement_event signals from the fidelización module,
detects cross-patient patterns via deterministic Python clustering,
and (when clusters exist) calls a single LLM completion (Kimi via
LiteLLM canonical post 2026-05-06) to phrase Owner-facing recommendations.

HIPAA-lite (vitalia/.claude/rules/hipaa-lite.md):
  * Dual filter tenant_id + clinic_id enforced by the consumed
    ReEngagementEventRepository (CompoundScopeRepositoryBase).
  * Aggregates contain ONLY counts — NEVER patient_id/name/email/phone.
  * recommendation text passes through engine `sanitize_payload`
    (luana_core_observability) defense-in-depth before returning.

Anti-duplication §0 (.claude/rules/anti-duplication.md):
  * `sanitize_payload` consumed from `luana_core_observability.recording.sanitization`
    — engine SSoT. NEVER re-implemented or mirrored per-brand.
  * LLM dispatch via `LiteLLMService.generate_response` (engine canonical).
    NEVER mirror provider adapters here.
  * ReEngagementEventRepository (T-4) consumed — NEVER raw session bypass.

Cache slot architecture (03-arch-agentic § 4.2):
  * SLOT 1+2 = system_prompt (Lucas role + Vitalia medical context + rubric +
    JSON output schema). CACHEABLE. NEVER includes tenant_id/clinic_id/timestamp
    (any tenant-scoped value would break prefix invariance).
  * SLOT 3 = user message (cluster aggregates + period). VARIABLE per invocation.
  * Cache TTL 1h (Lucas recommendation reused across multiple Owner views in hour).
"""

from __future__ import annotations

import json
import re
from typing import Any, Protocol
from uuid import UUID

import structlog
from luana_core_observability.recording.sanitization import sanitize_payload

logger = structlog.get_logger(__name__)


# ─── Protocols (decouple from concrete classes) ──────────────────────────


class ReEngagementEventRepoProtocol(Protocol):
    """Minimal protocol for re_engagement_event_repository.list_in_period."""

    async def list_in_period(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_days: int,
    ) -> list[Any]: ...


class LLMServiceProtocol(Protocol):
    """Protocol for LiteLLMService.generate_response (sync engine canonical)."""

    def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model_type: str = "smart",
        **kwargs: Any,
    ) -> str: ...


# ─── Prompt template (cacheable SLOT 1+2 — must be invariant per tenant) ─


_LUCAS_REENGAGEMENT_SYSTEM_PROMPT = (
    "Eres Lucas, un analista de fidelización para clínicas de salud y bienestar "
    "(vertical Vitalia). Tu rol es analizar patrones agregados de re-engagement "
    "(múltiples sesiones incompletas, follow-up vencido, mantenimiento omitido, "
    "ausencia prolongada, NPS reducido) y proponer acciones priorizadas para "
    "optimizar la fidelización del clinic.\n"
    "\n"
    "REGLAS HIPAA-lite (estrictas):\n"
    "- NUNCA menciones nombres de pacientes, IDs específicos, emails o teléfonos.\n"
    "- Trabaja SOLO con datos agregados: conteos, patrones, outcomes.\n"
    "- Las recomendaciones son a nivel de clínica, NO de paciente individual.\n"
    "\n"
    "FORMATO DE SALIDA (JSON estricto, NUNCA texto fuera del array):\n"
    "Devuelve un array JSON de objetos con esta forma exacta:\n"
    "[\n"
    "  {\n"
    '    "pattern": "<multi_session|follow_up|maintenance|absence|nps>",\n'
    '    "priority": "<high|medium|low>",\n'
    '    "action": "<accion concreta, espanol neutro tuteo, max 200 caracteres>",\n'
    '    "expected_impact_pct": <entero 1-100>,\n'
    '    "rationale": "<por que esta accion en base a las senales, max 300 caracteres>"\n'
    "  }\n"
    "]\n"
    "\n"
    "PRIORIZACION:\n"
    "- high: cluster con count >= 3 y outcome 'no_response' o 'opted_out'\n"
    "- medium: cluster con count 2 o outcome 'rescheduled'/'mixed'\n"
    "- low: cluster con count 1 o outcome positivo\n"
    "\n"
    "Espanol neutro latinoamericano sin voseo."
)


# ─── Service ─────────────────────────────────────────────────────────────


class LucasReEngagementService:
    """Application service for Lucas re-engagement recommendation tool.

    Pipeline (per 03-arch-agentic § 2.2):
        1. aggregate_patterns(tenant, clinic, period_days) → list[dict]
        2. detect_clusters(aggregates) → list[dict]  (Python deterministic)
        3. generate_recommendations(clusters) → list[dict]  (LLM single call)
        4. Apply sanitize_payload (defense-in-depth).

    Caller `run(...)` composes the full pipeline. Stateless — no persistence
    (Slice 1 minimal scope; Slice 2+ may persist if cron job needs).
    """

    # Cluster threshold (Python heuristic — KMeans/sklearn optional Slice 2+)
    _CLUSTER_COUNT_THRESHOLD = 2

    def __init__(
        self,
        *,
        re_engagement_repo: ReEngagementEventRepoProtocol,
        llm_service: LLMServiceProtocol,
    ) -> None:
        self._re_engagement_repo = re_engagement_repo
        self._llm_service = llm_service

    async def run(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_days: int = 30,
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        """Composite pipeline — aggregate → cluster → LLM → sanitize.

        Returns a list of recommendation dicts (at most `top_n`).
        Returns empty list when no clusters detected or LLM call fails.
        """
        aggregates = await self.aggregate_patterns(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period_days=period_days,
        )
        clusters = self.detect_clusters(aggregates)
        recommendations = await self.generate_recommendations(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            clusters=clusters,
            period_days=period_days,
            top_n=top_n,
        )
        return recommendations

    async def aggregate_patterns(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_days: int,
    ) -> list[dict[str, Any]]:
        """Aggregate re_engagement_events by (pattern, outcome) tuple.

        HIPAA-lite: dual filter tenant_id + clinic_id passed to repo.
        Output contains ONLY pattern + outcome + count (NO patient identifiers).
        """
        events = await self._re_engagement_repo.list_in_period(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period_days=period_days,
        )

        # Group by (pattern, outcome) tuple — count occurrences
        counts: dict[tuple[str, str | None], int] = {}
        for event in events:
            key = (event.pattern, event.outcome)
            counts[key] = counts.get(key, 0) + 1

        # Materialize as list of dicts (pattern + outcome + count ONLY)
        aggregates: list[dict[str, Any]] = [
            {"pattern": pattern, "outcome": outcome, "count": count} for (pattern, outcome), count in counts.items()
        ]
        # Stable order: highest count first then alphabetical pattern
        aggregates.sort(key=lambda a: (-a["count"], a["pattern"], a.get("outcome") or ""))
        return aggregates

    def detect_clusters(
        self,
        aggregates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Python deterministic clustering — NO LLM call.

        Heuristic Slice 1: any aggregate with count >= _CLUSTER_COUNT_THRESHOLD
        forms a cluster. Slice 2+ may upgrade to KMeans/sklearn.
        """
        clusters = [agg for agg in aggregates if agg.get("count", 0) >= self._CLUSTER_COUNT_THRESHOLD]
        # Already sorted by aggregate_patterns; preserve order
        return clusters

    async def generate_recommendations(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        clusters: list[dict[str, Any]],
        period_days: int,
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        """Single LLM call → parsed recommendations list.

        Cost guard: NO LLM call if no clusters (returns []).
        Graceful: LLM failures return [] without raising (best-effort).
        Sanitization: applied to each recommendation dict (defense-in-depth).
        """
        if not clusters:
            return []

        # Build user message (SLOT 3 — variable per invocation)
        user_payload = {
            "period_days": period_days,
            "top_n": top_n,
            "clusters": clusters,
        }
        user_message = (
            "Analiza estos clusters de senales de re-engagement y devuelve "
            "hasta " + str(top_n) + " recomendaciones priorizadas en formato JSON "
            "estricto (sin texto fuera del array). Datos:\n" + json.dumps(user_payload, ensure_ascii=False)
        )

        try:
            raw_llm_text = self._llm_service.generate_response(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=_LUCAS_REENGAGEMENT_SYSTEM_PROMPT,
                model_type="smart",
            )
        except Exception as exc:  # noqa: BLE001 — graceful degradation per arch § 4.3
            logger.warning(
                "lucas_re_engagement_llm_error",
                exc=str(exc),
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                cluster_count=len(clusters),
            )
            return []

        parsed = _parse_llm_recommendations(raw_llm_text)
        if not parsed:
            logger.warning(
                "lucas_re_engagement_llm_unparseable",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                raw_preview=raw_llm_text[:200],
            )
            return []

        # Truncate to top_n
        truncated = parsed[:top_n]

        # Sanitize each recommendation dict via engine SSoT (defense-in-depth)
        sanitized: list[dict[str, Any]] = [sanitize_payload(rec) for rec in truncated]

        logger.info(
            "lucas_re_engagement_recommendations_generated",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            cluster_count=len(clusters),
            recommendation_count=len(sanitized),
        )
        return sanitized


# ─── Helpers ─────────────────────────────────────────────────────────────


# Regex to find the first JSON array in LLM output (defensive: LLMs may wrap
# JSON in markdown code fences or preamble text despite explicit instructions).
_JSON_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)


def _parse_llm_recommendations(raw_text: str) -> list[dict[str, Any]]:
    """Parse LLM output into a list of recommendation dicts.

    Tolerates markdown fences and extra preamble. Returns [] on failure.
    Each recommendation MUST have keys: pattern, priority, action,
    expected_impact_pct, rationale. Malformed entries are dropped.
    """
    if not raw_text:
        return []

    match = _JSON_ARRAY_RE.search(raw_text)
    if not match:
        return []

    try:
        parsed = json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return []

    if not isinstance(parsed, list):
        return []

    required_keys = {"pattern", "priority", "action", "expected_impact_pct", "rationale"}
    valid: list[dict[str, Any]] = []
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        if not required_keys.issubset(entry.keys()):
            continue
        # Coerce expected_impact_pct to int (LLM may return float)
        try:
            entry["expected_impact_pct"] = int(entry["expected_impact_pct"])
        except (TypeError, ValueError):
            continue
        valid.append(entry)
    return valid


__all__ = [
    "LLMServiceProtocol",
    "LucasReEngagementService",
    "ReEngagementEventRepoProtocol",
]
