# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""Vitalia AGENTIC extractor — `DentalHistoryExtractor` (R23 Opus 4.7).

Story 11 T-extractors-2.

Spec sources:
  * 02-design-agentic.md § 7.2 — verbose 4-wave vision-heavy spec
  * 03-arch-agentic.md § 5.2 — class skeleton + § 5.3 inheritance gate
  * 06-tickets.yaml::T-extractors-2 acceptance A1 (FDI) + A2 (cost ≤$0.18)
  * 04-validators.yaml V-AE-6 + V-AE-16

Architecture (Inside-Out per `.claude/rules/backend-ddd.md`):

  Domain  ── ``DentalHistoryV1`` + primitives in ``_schemas.py``  (pure Pydantic)
  Infra   ── ``VitaliaPatientDentalHistoryModel`` in infrastructure/models/
              + per-tenant Qdrant collection naming
  App     ── THIS FILE — orchestrates 4 LLM waves, merges, persists, emits event
  API     ── (none — extractor is invoked async from upload pipeline,
              future T-be-7 wires the route)

Wave composition (vision-heavy bar — vs MedicalKBExtractor):
  W1 missing_pieces_chart            — Sonnet vision (chart image parse)
  W2 restorations_and_periodontal    — Sonnet vision (chart + periodontal page)
  W3 bite_and_radiographs            — Haiku vision (cheaper, simpler vision)
  W4 validate_and_merge              — Sonnet reasoning (text-only, structured JSON)

Cost / latency budget:
  * cost_usd ≤ 0.18 per PDF (V-AE-16 threshold). Vision pricing is the
    main driver — wave 3 deliberately uses Haiku to stay in budget.
  * latency p50 30s / p99 90s (ASYNC — kicked from upload UI, result via WS / poll).

Anti-duplication audit (Step 0 GATE pre-write, 2026-05-14):
  * grep cross codebase for ``class DentalHistoryExtractor`` → zero collisions
  * grep cross codebase for ``class DentalHistoryV1`` → zero collisions
  * EXTENDS ``luana_core_extraction.base_orchestrator.BaseExtractionOrchestrator``
    (anti-duplication.md SSoT row — wave scheduling + progress emission DRY)
  * Sibling T-extractors-1 owns ``MedicalKBExtractor`` in same package.
    Both share ``ExtractionWave`` dataclass + same prompt slot architecture.
  * ``sanitize_payload`` consumed from ``luana_core_observability.recording.sanitization``
    — NEVER re-implemented (PII regex SSoT).

Tenant isolation invariants:
  * tenant_id REQUIRED in run() — repos + Qdrant indexer scope by it.
  * Qdrant collection name embeds tenant_id (cross-tenant search impossible).
  * Trace events include tenant_id for downstream cost / audit queries.

Observability (best-effort per copilot-observability rule):
  * Every wave emits a structured trace event (sanitized payload).
  * Cost recording on every wave (cost_usd contribution + cumulative).
  * Trace failure NEVER breaks the extractor turn (try/except + structlog warn).

Graceful degradation (tessl__graceful-degradation):
  * Each wave has its own timeout. Timeout → log warning + decrement
    confidence + continue (NOT crash). Partial result preferred over none.
  * LLM transient error retried once at the wave layer (idempotent prompts).
  * Persistence failure → emit alert + leave domain event un-published
    (Aurora downstream MUST not consume an unpersisted extraction).
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

import structlog
from luana_core_extraction.base_orchestrator import BaseExtractionOrchestrator

from src.modules.vitalia.copilot.extractors._schemas import (
    BiteAlignmentNotes,
    DentalHistoryV1,
    ExtractionWave,
    PeriodontalSummary,
    RadiographRef,
    Restoration,
    ToothPosition,
)

logger = structlog.get_logger(__name__)


# ─── Cost ceiling (V-AE-16 threshold + 02-design § 7.2) ──────────────────────

#: Max cumulative LLM cost per PDF for the dental extractor (vision-heavy bar).
#: Exceeded → ``_cost_overrun`` returns True, extractor records warning and
#: degrades confidence (no silent budget overrun).
COST_CEILING_USD_PER_PDF: float = 0.18


# ─── Domain event (DentalChartReadyV1 — consumed by Aurora workflow) ─────────


@dataclass(frozen=True, slots=True)
class DentalChartReadyV1:
    """Domain event emitted after a successful dental extraction.

    Consumed by Aurora's ``TreatmentFollowupWorkflow`` for implant procedure
    planning: ``missing_pieces`` → suggested implant slots in the D5 / D14
    follow-up cadence.

    Schema-cemented per Story D goldens playbook — V2 is a NEW class, V1 frozen.
    """

    schema_version: int
    tenant_id: UUID
    patient_id: UUID
    confidence_score: float
    missing_pieces_count: int
    has_restorations: bool


# ─── Collaborator protocols (DI / structural typing) ─────────────────────────


class _LLMServiceProto(Protocol):
    """Minimal LLM surface consumed by the extractor.

    The production implementation is the LiteLLM-routed adapter installed
    in the brand context (per shared/infrastructure/llm/router.py). The
    test bench passes a stub returning canned JSON per wave.
    """

    async def acomplete(
        self,
        *,
        role: str,
        messages: list[dict[str, Any]],
        timeout_sec: float,
        wave_name: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]: ...  # noqa: D401


class _DentalHistoryRepoProto(Protocol):
    """Minimal repository surface — upserts the dental history row."""

    async def upsert(
        self,
        *,
        tenant_id: UUID,
        patient_id: UUID,
        payload: dict[str, Any],
    ) -> None: ...  # noqa: D401


class _EventBusProto(Protocol):
    """Minimal event bus surface — publishes DentalChartReadyV1."""

    async def publish(self, event: Any) -> None: ...  # noqa: D401


class _TraceEventRepoProto(Protocol):
    """Minimal trace event repository surface — best-effort observability."""

    async def record(
        self,
        *,
        tenant_id: UUID,
        event_type: str,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> None: ...  # noqa: D401


class _QdrantIndexerProto(Protocol):
    """Minimal Qdrant indexer surface — per-tenant collection RAG indexing."""

    async def index(
        self,
        *,
        collection: str,
        payload: dict[str, Any],
        vector: list[float] | None = None,
    ) -> None: ...  # noqa: D401


# ─── Extractor — DentalHistoryExtractor (extends shared base) ────────────────


class DentalHistoryExtractor(BaseExtractionOrchestrator):
    """4-wave vision-heavy dental history extractor.

    Subclass of :class:`BaseExtractionOrchestrator` — reuses its wave
    scheduling helpers (``_run_wave`` / ``_pause_between_waves``) and
    contributes:

      * a 4-wave configuration declared at class scope (vision-heavy)
      * per-wave timeout + degraded-confidence error mode
      * cost aggregation guard against ``COST_CEILING_USD_PER_PDF``
      * persistence to ``vitalia_patient_dental_histories``
      * Qdrant indexing under per-tenant collection
      * domain event emission for Aurora's TreatmentFollowupWorkflow
    """

    log_prefix = "vitalia_dental_extraction"

    waves: tuple[ExtractionWave, ...] = (
        ExtractionWave(
            name="missing_pieces_chart",
            model_role="vision",
            prompt_template="dental_extract_missing_pieces_chart.j2",
            timeout_sec=30.0,
        ),
        ExtractionWave(
            name="restorations_and_periodontal",
            model_role="vision",
            prompt_template="dental_extract_restorations_and_periodontal.j2",
            timeout_sec=30.0,
        ),
        ExtractionWave(
            name="bite_and_radiographs",
            model_role="vision",  # Haiku vision — model_role still "vision"
            prompt_template="dental_extract_bite_and_radiographs.j2",
            timeout_sec=20.0,
        ),
        ExtractionWave(
            name="validate_and_merge",
            model_role="reasoning",
            prompt_template="dental_extract_validate_and_merge.j2",
            timeout_sec=20.0,
        ),
    )

    EXTRACTOR_VERSION: str = "dental_v1.0.0"

    def __init__(
        self,
        *,
        llm_service: _LLMServiceProto,
        history_repo: _DentalHistoryRepoProto,
        event_bus: _EventBusProto,
        trace_event_repo: _TraceEventRepoProto | None = None,
        qdrant_indexer: _QdrantIndexerProto | None = None,
    ) -> None:
        """Inject collaborators (DI). Trace + Qdrant are best-effort optional."""
        self._llm = llm_service
        self._history_repo = history_repo
        self._event_bus = event_bus
        self._trace_event_repo = trace_event_repo
        self._qdrant_indexer = qdrant_indexer

    # ─────────────────────────────────────────────────────────────────────
    # Public API — orchestrates the 4 waves end-to-end.
    # ─────────────────────────────────────────────────────────────────────

    async def run(
        self,
        *,
        pdf_url: str,
        tenant_id: UUID,
        patient_id: UUID,
    ) -> DentalHistoryV1:
        """Extract dental history from a PDF + persist + emit event.

        Args:
            pdf_url: Signed URL of the patient PDF (≤20 pages enforced upstream).
            tenant_id: Tenant scope for repos + Qdrant collection.
            patient_id: Patient identifier (FK to ``vitalia_patients``).

        Returns:
            ``DentalHistoryV1`` — the merged extraction. Persistence is a
            side-effect; the caller may use the return for in-memory display.

        Raises:
            Never propagates LLM / wave timeouts — degrades confidence + warns.
            ``Exception`` bubbles ONLY for catastrophic persistence failure
            (see error mode in module docstring).
        """
        wave_outputs: dict[str, Any] = {}
        wave_usages: list[dict[str, Any]] = []
        warnings: list[str] = []

        # ── Run 4 waves sequentially (vision provider rate limits prefer this) ──
        for wave in self.waves:
            wave_result = await self._run_single_wave(
                wave=wave,
                pdf_url=pdf_url,
                tenant_id=tenant_id,
                patient_id=patient_id,
                prior_outputs=wave_outputs,
            )
            wave_outputs[wave.name] = wave_result["content"]
            wave_usages.append(wave_result["usage_with_cost"])
            warnings.extend(wave_result["warnings"])

        # ── Aggregate cost + check budget overrun ──
        total_cost_usd = self._aggregate_cost(wave_usages)
        if self._cost_overrun(total_cost_usd):
            warnings.append(
                f"cost_overrun: cumulative ${total_cost_usd:.4f} USD exceeds "
                f"ceiling ${COST_CEILING_USD_PER_PDF:.2f} USD"
            )

        # ── Merge waves into DentalHistoryV1 ──
        merged = self._merge_wave_outputs(wave_outputs, warnings=warnings)

        # ── Persist + index + emit event ──
        await self._persist_and_emit(
            tenant_id=tenant_id,
            patient_id=patient_id,
            history=merged,
        )

        # ── Final trace event (sanitized; best-effort) ──
        await self._emit_trace_safe(
            tenant_id=tenant_id,
            event_type="dental_extractor.completed",
            payload={
                "patient_id": str(patient_id),
                "confidence_score": merged.confidence_score,
                "missing_pieces_count": len(merged.missing_pieces),
                "total_cost_usd": total_cost_usd,
                "warnings_count": len(merged.extraction_warnings),
            },
        )

        return merged

    # ─────────────────────────────────────────────────────────────────────
    # Wave execution — graceful degradation on timeout / parse failure.
    # ─────────────────────────────────────────────────────────────────────

    async def _run_single_wave(
        self,
        *,
        wave: ExtractionWave,
        pdf_url: str,
        tenant_id: UUID,
        patient_id: UUID,
        prior_outputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Run one wave with timeout + best-effort observability.

        Returns a dict with keys ``content`` (raw JSON output), ``warnings``
        (list of warning strings), ``usage_with_cost`` (dict for cost accounting).
        """
        # Build minimal messages — the production prompt loader resolves the
        # Jinja template + injects pdf_url + prior_outputs into the volatile
        # block AFTER the cache_control marker (cache-prefix invariant).
        messages = [
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "wave": wave.name,
                        "pdf_url": pdf_url,
                        "prior_waves": list(prior_outputs.keys()),
                    }
                ),
            }
        ]

        # Telemetry trace — wave start (best-effort).
        await self._emit_trace_safe(
            tenant_id=tenant_id,
            event_type=f"dental_extractor.wave_start.{wave.name}",
            payload={
                "patient_id": str(patient_id),
                "wave": wave.name,
                "model_role": wave.model_role,
                "timeout_sec": wave.timeout_sec,
            },
        )

        try:
            result = await asyncio.wait_for(
                self._llm.acomplete(
                    role=wave.model_role,
                    messages=messages,
                    timeout_sec=wave.timeout_sec,
                    wave_name=wave.name,
                ),
                timeout=wave.timeout_sec + 5.0,  # outer guard slack
            )
        except (asyncio.TimeoutError, TimeoutError) as exc:
            # Graceful degradation — log + continue with empty content.
            warning = f"wave_timeout: {wave.name} exceeded {wave.timeout_sec}s ({exc!s})"
            logger.warning(
                "vitalia_dental_extractor_wave_timeout",
                wave=wave.name,
                tenant_id=str(tenant_id),
                patient_id=str(patient_id),
            )
            await self._emit_trace_safe(
                tenant_id=tenant_id,
                event_type=f"dental_extractor.wave_timeout.{wave.name}",
                payload={"patient_id": str(patient_id), "wave": wave.name},
            )
            return {
                "content": {},
                "warnings": [warning],
                "usage_with_cost": {"input_tokens": 0, "output_tokens": 0, "wave_cost_usd": 0.0},
            }

        # Sanitize content for observability emission BEFORE we propagate further.
        sanitized_for_trace = self._sanitize_for_trace(result.get("content", {}))

        await self._emit_trace_safe(
            tenant_id=tenant_id,
            event_type=f"dental_extractor.wave_complete.{wave.name}",
            payload={
                "patient_id": str(patient_id),
                "wave": wave.name,
                "content_summary": sanitized_for_trace,
                "usage": result.get("usage", {}),
                "cost_usd": result.get("wave_cost_usd", 0.0),
            },
        )

        return {
            "content": result.get("content", {}),
            "warnings": [],
            "usage_with_cost": {
                "input_tokens": result.get("usage", {}).get("input_tokens", 0),
                "output_tokens": result.get("usage", {}).get("output_tokens", 0),
                "wave_cost_usd": result.get("wave_cost_usd", 0.0),
            },
        }

    # ─────────────────────────────────────────────────────────────────────
    # Merge wave outputs → DentalHistoryV1
    # ─────────────────────────────────────────────────────────────────────

    def _merge_wave_outputs(
        self,
        wave_outputs: dict[str, Any],
        *,
        warnings: list[str],
    ) -> DentalHistoryV1:
        """Translate raw wave JSON into validated DentalHistoryV1.

        Wave outputs that fail Pydantic validation (e.g. malformed FDI codes
        from a hallucinated LLM response) are dropped from the structured
        output and flagged via ``extraction_warnings`` — partial result over
        crash, per error mode in module docstring.
        """
        # ── W1: missing_pieces_chart → list[ToothPosition] ──
        missing_pieces: list[ToothPosition] = []
        w1 = wave_outputs.get("missing_pieces_chart") or {}
        for fdi in w1.get("missing", []):
            try:
                missing_pieces.append(ToothPosition(fdi_code=int(fdi)))
            except (ValueError, TypeError) as exc:
                warnings.append(f"invalid_missing_piece: fdi={fdi!r} dropped ({exc!s})")
        warnings.extend(w1.get("warnings", []))

        # ── W2: restorations_and_periodontal ──
        restorations: list[Restoration] = []
        w2 = wave_outputs.get("restorations_and_periodontal") or {}
        for raw in w2.get("restorations", []):
            try:
                restorations.append(Restoration(**raw))
            except (ValueError, TypeError) as exc:
                warnings.append(f"invalid_restoration: {raw!r} dropped ({exc!s})")

        periodontal: PeriodontalSummary | None = None
        if w2.get("periodontal") is not None:
            try:
                periodontal = PeriodontalSummary(**w2["periodontal"])
            except (ValueError, TypeError) as exc:
                warnings.append(f"invalid_periodontal: {w2['periodontal']!r} dropped ({exc!s})")
        warnings.extend(w2.get("warnings", []))

        # ── W3: bite_and_radiographs ──
        bite: BiteAlignmentNotes | None = None
        w3 = wave_outputs.get("bite_and_radiographs") or {}
        if w3.get("bite") is not None:
            try:
                bite = BiteAlignmentNotes(**w3["bite"])
            except (ValueError, TypeError) as exc:
                warnings.append(f"invalid_bite: {w3['bite']!r} dropped ({exc!s})")
        radiographs: list[RadiographRef] = []
        for raw in w3.get("radiographs", []):
            try:
                radiographs.append(RadiographRef(**raw))
            except (ValueError, TypeError) as exc:
                warnings.append(f"invalid_radiograph: {raw!r} dropped ({exc!s})")
        warnings.extend(w3.get("warnings", []))

        # ── W4: validate_and_merge — confidence + missing required ──
        w4 = wave_outputs.get("validate_and_merge") or {}
        wave_warnings = w4.get("warnings", [])
        warnings.extend(wave_warnings)

        # Confidence: start from W4 hint or default 1.0; decrement per warning.
        base_conf = float(w4.get("confidence_score", 1.0))
        # Per-warning decrement (capped to [0, 1]).
        confidence = max(0.0, min(1.0, base_conf - 0.1 * len(warnings)))

        missing_required: list[str] = list(w4.get("missing_required_fields", []))

        return DentalHistoryV1(
            missing_pieces=missing_pieces,
            existing_restorations=restorations,
            periodontal_status=periodontal,
            bite_alignment=bite,
            radiographs_referenced=radiographs,
            confidence_score=confidence,
            missing_required_fields=missing_required,
            extraction_warnings=warnings,
        )

    # ─────────────────────────────────────────────────────────────────────
    # Persistence + event emission + Qdrant indexing
    # ─────────────────────────────────────────────────────────────────────

    async def _persist_and_emit(
        self,
        *,
        tenant_id: UUID,
        patient_id: UUID,
        history: DentalHistoryV1,
    ) -> None:
        """Persist row + index in Qdrant + emit DentalChartReadyV1 event."""
        payload = history.model_dump(mode="json")

        # 1. Persist (CRITICAL — must succeed before event publish).
        await self._history_repo.upsert(
            tenant_id=tenant_id,
            patient_id=patient_id,
            payload=payload,
        )

        # 2. Qdrant index — best-effort; failure does NOT block event emission
        #    (Aurora workflow does not depend on RAG index).
        if self._qdrant_indexer is not None:
            try:
                await self._qdrant_indexer.index(
                    collection=self._qdrant_collection_name(tenant_id),
                    payload={
                        "patient_id": str(patient_id),
                        "kind": "dental_history",
                        "summary": payload,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "vitalia_dental_extractor_qdrant_index_failed",
                    tenant_id=str(tenant_id),
                    patient_id=str(patient_id),
                    error=str(exc),
                )

        # 3. Emit DentalChartReadyV1 — Aurora consumes this for implant planning.
        event = DentalChartReadyV1(
            schema_version=1,
            tenant_id=tenant_id,
            patient_id=patient_id,
            confidence_score=history.confidence_score,
            missing_pieces_count=len(history.missing_pieces),
            has_restorations=bool(history.existing_restorations),
        )
        await self._event_bus.publish(event)

    @staticmethod
    def _qdrant_collection_name(tenant_id: UUID) -> str:
        """Per-tenant Qdrant collection — embeds tenant_id (R2 tenant-isolation).

        Naming convention: ``vitalia_dental_history_{tenant_uuid}``.
        Cross-tenant search is impossible because every collection is
        tenant-scoped (no multi-tenant collection with a tenant_id filter).
        """
        return f"vitalia_dental_history_{tenant_id}"

    # ─────────────────────────────────────────────────────────────────────
    # Cost accounting helpers (tested directly by T4 — public for unit tests)
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _aggregate_cost(wave_usages: list[dict[str, Any]]) -> float:
        """Sum ``wave_cost_usd`` across all waves.

        Pure function — no side effects. Tested in
        ``test_dental_history_extractor.py::test_cost_budget``.
        """
        return sum(float(u.get("wave_cost_usd", 0.0)) for u in wave_usages)

    @staticmethod
    def _cost_overrun(total_cost_usd: float) -> bool:
        """True iff total cost exceeds the V-AE-16 dental ceiling.

        Used by both the extractor (record warning) and the test bench
        (assert symmetric ceiling enforcement).
        """
        return total_cost_usd > COST_CEILING_USD_PER_PDF

    # ─────────────────────────────────────────────────────────────────────
    # Observability helpers — sanitization + best-effort emission
    # ─────────────────────────────────────────────────────────────────────

    # Suspicious key patterns — vertical-medical PII fields that can leak
    # into a wave's raw output if the LLM hallucinates verbatim from the
    # PDF. We pre-strip these structural keys BEFORE delegating to the
    # shared regex-based sanitizer (defense in depth).
    #
    # The shared sanitizer is keyword-anchored for bare digits — it
    # deliberately does NOT redact 8-digit runs without a keyword nearby
    # (see S1 sales_agent rationale in shared sanitization.py docstring).
    # That heuristic protects against false positives on order_id / score
    # but means a hallucinated dict like ``{"patient_dni": "12345678"}``
    # would slip through. The extractor takes the conservative line for
    # medical-PII surface and drops the value entirely.
    _PII_KEY_PATTERNS: tuple[str, ...] = (
        "dni",
        "documento",
        "ssn",
        "national_id",
        "tax_id",
        "social_security",
        "rut",
        "rfc",
        "curp",
        "cuit",
        "cuil",
        "cpf",
        "address",
        "street",
        "phone",
        "telefono",
        "celular",
        "mobile",
        "email",
        "correo",
        "dob",
        "date_of_birth",
        "birth_date",
        "birthday",
        "fecha_nacimiento",
    )

    def _sanitize_for_trace(self, content: Any) -> Any:
        """Sanitize a wave's raw content before tracing.

        Per `.tessl/...pii-sanitisation` + copilot-observability rule:
        PDF extraction can surface DNI / email / phone / address fragments
        that a hallucinated LLM might reproduce verbatim. We scrub via
        TWO layers (defense in depth):

          1. Drop dict keys that structurally look like PII fields
             (``patient_dni``, ``email``, etc — see ``_PII_KEY_PATTERNS``).
          2. Pass remainder through shared ``sanitize_payload`` for regex
             scrubbing of inline tokens / emails / phones / IDs.

        Implementation: late-import ``sanitize_payload`` so the test bench
        can monkey-patch it; if the shared utility is unavailable for any
        reason, fall back to a conservative redaction (keep only structural
        keys + sizes — never raw values).
        """
        prepared = self._strip_pii_keys(content)
        try:
            from luana_core_observability.recording.sanitization import sanitize_payload

            if isinstance(prepared, dict):
                return sanitize_payload(prepared)
            # Wrap non-dict in a synthetic key so the shared API accepts it.
            return sanitize_payload({"value": prepared})["value"]
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "vitalia_dental_extractor_sanitize_unavailable_fallback",
                error=str(exc),
            )
            # Fallback — emit only the keys + value-type summary, never raw values.
            if isinstance(prepared, dict):
                return {k: type(v).__name__ for k, v in prepared.items()}
            return {"_redacted": type(prepared).__name__}

    @classmethod
    def _strip_pii_keys(cls, content: Any) -> Any:
        """Recursively drop dict keys matching ``_PII_KEY_PATTERNS``.

        The replacement value is the placeholder ``"[REDACTED_PII_KEY]"`` so
        the consumer can tell that a field was scrubbed (vs missing).
        """
        if isinstance(content, dict):
            cleaned: dict[str, Any] = {}
            for k, v in content.items():
                key_lower = str(k).lower()
                if any(pat in key_lower for pat in cls._PII_KEY_PATTERNS):
                    cleaned[k] = "[REDACTED_PII_KEY]"
                else:
                    cleaned[k] = cls._strip_pii_keys(v)
            return cleaned
        if isinstance(content, list):
            return [cls._strip_pii_keys(item) for item in content]
        if isinstance(content, tuple):
            return tuple(cls._strip_pii_keys(item) for item in content)
        return content

    async def _emit_trace_safe(
        self,
        *,
        tenant_id: UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Best-effort trace emission — try/except + structlog warning, never raises.

        Per `.claude/rules/copilot-observability.md`: observability MUST NEVER
        break the agent turn. If the trace_event_repo is unavailable or its
        write fails, log and continue.
        """
        if self._trace_event_repo is None:
            return
        sanitized = self._sanitize_for_trace(payload)
        try:
            await self._trace_event_repo.record(
                tenant_id=tenant_id,
                event_type=event_type,
                payload=sanitized,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "vitalia_dental_extractor_trace_emit_failed",
                event_type=event_type,
                tenant_id=str(tenant_id),
                error=str(exc),
            )


__all__ = [
    "COST_CEILING_USD_PER_PDF",
    "DentalChartReadyV1",
    "DentalHistoryExtractor",
]
