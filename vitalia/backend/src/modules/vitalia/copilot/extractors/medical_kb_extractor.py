# cap: copilot.medical-kb-rag
# story-origin: TBD
"""Vitalia AGENTIC extractor — `MedicalKBExtractor` (T-extractors-1, R23 Opus 4.7).

EXTENDS ``luana_core_extraction.base_orchestrator.BaseExtractionOrchestrator`` per
``.claude/rules/anti-duplication.md`` SSoT row (wave-based LLM extraction lift
shared, NOT mirror).

4-wave pipeline (per 03-arch-agentic § 5.1):
  W1  allergies_and_medications     vision Sonnet  ≤30 s
  W2  conditions_and_surgeries      vision Sonnet  ≤30 s
  W3  family_and_vitals             vision Haiku   ≤20 s
  W4  validate_and_merge            text   Sonnet  ≤20 s

Cost budget: ≤$0.15 USD per PDF (V-AE-16). Latency: p50 25 s / p99 70 s.

Side-effects (best-effort, never break extractor turn):
  * Persist ``vitalia_patient_medical_histories`` row (tenant-isolated repo).
  * Index structured JSON to Qdrant per-tenant collection (RAG context).
  * Emit ``MedicalHistoryExtractedV1`` domain event (outbox pattern).
  * Audit_log ``medical_pii_extracted_from_upload`` (compliance).

All side-effects wrapped in ``try/except + structlog.warning`` per R23 — failure
to persist or index MUST NOT raise extractor exceptions. Extractor turn is
"successful" iff at least one wave produced a partial output (degraded
``confidence_score`` reflects quality).

Tenant isolation (R2): ``tenant_id`` + ``patient_id`` are run-time inputs.
Repo binds tenant in constructor; Qdrant collection is per-tenant; outbox event
carries tenant_id.

PII handling:
  * Patient PDF text never logged verbatim — ``sanitize_payload`` redacts emails,
    phone numbers, and provider tokens before observability writes.
  * Wave outputs ARE persisted (that IS the structured medical history product),
    but the JSONB ``extracted_payload`` column is the data contract — observability
    payloads only carry summaries (counts + confidence + warnings).

Anti-duplication audit (Step 0 GATE pre-write, 2026-05-14):
  * ``grep -rn "class MedicalKBExtractor"`` cross luana-platform + AISALESHT
    backend → zero collisions.
  * Wave + sleep + progress mechanics consumed from ``BaseExtractionOrchestrator``
    (luana_core_extraction). NEVER re-implemented.
  * ``sanitize_payload`` consumed from ``luana_core_observability.recording.sanitization``.
  * ``pop_cost`` consumed from ``luana_core_observability.recording.cost_recorder``
    (LiteLLM CustomLogger bridge per PI-12 S1 T-1 cement).

Spec sources:
  * 02-design-agentic.md § 7.1
  * 03-arch-agentic.md § 5.1
  * 04-validators.yaml V-AE-6 + V-AE-16
  * 06-tickets.yaml::T-extractors-1 acceptance A1-A3
  * 05-guidelines.md § 1.10 R23
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

import structlog
from luana_core_extraction.base_orchestrator import BaseExtractionOrchestrator
from luana_core_observability.recording.cost_recorder import pop_cost
from luana_core_observability.recording.sanitization import sanitize_payload

from src.modules.vitalia.copilot.extractors._schemas import (
    Allergy,
    Condition,
    ExtractionWave,
    FamilyHistorySummary,
    MedicalHistoryV1,
    Medication,
    Surgery,
    VitalSigns,
)

logger = structlog.get_logger(__name__)

# ─── Configuration constants ─────────────────────────────────────────────


_PROMPTS_DIR: Path = Path(__file__).parent / "_prompts"

# Confidence weighting per wave (sums to 1.0). Wave 4 (validate_and_merge) only
# adjusts via validation_score_adjustment — it does NOT contribute base score.
_WAVE_CONFIDENCE_WEIGHTS: dict[str, float] = {
    "allergies_and_medications": 0.35,
    "conditions_and_surgeries": 0.35,
    "family_and_vitals": 0.20,
    "validate_and_merge": 0.10,
}

# Per-wave hard cost ceiling (defensive). Sum ≤ V-AE-16 budget $0.15 USD.
_PER_WAVE_COST_CEILING_USD: dict[str, Decimal] = {
    "allergies_and_medications": Decimal("0.05"),
    "conditions_and_surgeries": Decimal("0.05"),
    "family_and_vitals": Decimal("0.03"),
    "validate_and_merge": Decimal("0.02"),
}

# Total PDF extraction cost ceiling — V-AE-16 SSoT. Caller can lower via
# constructor kwarg; raising requires CONTRACT bump.
DEFAULT_COST_BUDGET_USD: Decimal = Decimal("0.15")

# Minimum confidence below which the extractor flags for clinic_owner manual
# review (08-design-agentic § 5 edge 5: confidence < 0.7 → notification).
MIN_ACCEPTABLE_CONFIDENCE: float = 0.7

# Extractor schema version cement — emitted in domain event + audit log.
EXTRACTOR_VERSION: str = "medical_kb_v1"


# ─── Repository / client protocols (decouple from concrete types) ──────


class _LiteLLMServiceLike(Protocol):
    """Minimal surface consumed from LiteLLM-backed chat service.

    Subset of ``luana_core_llm.providers.litellm.LiteLLMService`` — only the
    methods exercised by the extractor are declared, so test fakes only need
    to implement those.
    """

    async def ainvoke_text(
        self,
        *,
        role: str,
        prompt: str,
        timeout_sec: float,
    ) -> "_LLMResponse": ...


@dataclass(frozen=True, slots=True)
class _LLMResponse:
    """LLM call result — text content + LiteLLM call_id for cost recovery."""

    content: str
    """Raw text content returned by the LLM (expected JSON for our prompts)."""

    litellm_call_id: str | None
    """LiteLLM call ID for ``pop_cost`` lookup. ``None`` when the proxy did
    not surface a call_id (cost considered unknown — still bounded by
    ``_PER_WAVE_COST_CEILING_USD`` budget)."""

    duration_ms: int = 0
    """Wall-clock duration for the LLM call (informational)."""


class _PatientMedicalHistoryRepoLike(Protocol):
    """Minimal surface consumed from PatientMedicalHistoryRepository (T-be-3)."""

    async def save_medical(self, history: Any) -> None: ...


class _QdrantIndexerLike(Protocol):
    """Minimal surface for indexing structured medical history into Qdrant.

    Per 02-design § 7.1 side-effect (b): "Indexes structured JSON to Qdrant
    per-tenant collection for RAG". Tenant-isolated by collection name.
    """

    async def index_medical_history(
        self,
        *,
        tenant_id: uuid.UUID,
        patient_id: uuid.UUID,
        history_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> None: ...


class _OutboxLike(Protocol):
    """Minimal surface for outbox-pattern event emission.

    Per 02-design § 7.1 side-effect (c): "Emits domain event MedicalHistoryExtracted".
    Outbox pattern (USE_OUTBOX_PATTERN_* default True per 2026-04-29 cutover) —
    NEVER use legacy EventBus.publish.
    """

    async def publish(
        self,
        *,
        event_type: str,
        tenant_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> None: ...


class _AuditLogLike(Protocol):
    """Minimal surface for medical audit_log writes.

    Per 02-design § 7.1 side-effect (d): "Audit_log medical_pii_extracted_from_upload".
    """

    async def log(
        self,
        *,
        tenant_id: uuid.UUID,
        patient_id: uuid.UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> None: ...


# ─── Extractor (extends BaseExtractionOrchestrator) ────────────────────────


class MedicalKBExtractor(BaseExtractionOrchestrator):
    """Wave-based extraction of patient medical history from PDF.

    Subclass concerns (per BaseExtractionOrchestrator contract):
      * ``run(...)`` — entry point.
      * ``_define_waves()`` — wave configuration.
      * ``_merge_and_save(...)`` — domain entity persistence.

    Wave scheduling + progress emission consumed from base.
    """

    log_prefix = "vitalia_medical_kb_extraction"
    default_wave_delay_seconds: float = 0.0  # Vision waves are LLM-bound; no inter-wave throttle needed.

    def __init__(
        self,
        *,
        llm_service: _LiteLLMServiceLike,
        history_repo: _PatientMedicalHistoryRepoLike,
        qdrant_indexer: _QdrantIndexerLike | None = None,
        outbox: _OutboxLike | None = None,
        audit_log: _AuditLogLike | None = None,
        cost_budget_usd: Decimal = DEFAULT_COST_BUDGET_USD,
    ) -> None:
        """Initialise extractor with required + optional collaborators.

        Required:
          ``llm_service``, ``history_repo``.
        Optional (best-effort side-effects when supplied):
          ``qdrant_indexer``, ``outbox``, ``audit_log``.

        ``cost_budget_usd`` defaults to V-AE-16 SSoT (0.15 USD). Lower via
        kwarg for cost-sensitive tenants; raising requires CONTRACT bump.
        """
        self._llm = llm_service
        self._history_repo = history_repo
        self._qdrant = qdrant_indexer
        self._outbox = outbox
        self._audit_log = audit_log
        self._cost_budget_usd = cost_budget_usd
        self._waves = self._define_waves()
        self._prompt_cache: dict[str, str] = {}

    # ----------------------------------------------------------------------
    # Wave definition (subclass concern)
    # ----------------------------------------------------------------------

    @staticmethod
    def _define_waves() -> list[ExtractionWave]:
        """Return the 4 waves that compose the medical-history extraction."""
        return [
            ExtractionWave(
                name="allergies_and_medications",
                model_role="vision",
                prompt_template="medical_extract_allergies_meds.j2",
                timeout_sec=30.0,
            ),
            ExtractionWave(
                name="conditions_and_surgeries",
                model_role="vision",
                prompt_template="medical_extract_conditions_surgeries.j2",
                timeout_sec=30.0,
            ),
            ExtractionWave(
                name="family_and_vitals",
                model_role="nano",  # Haiku via LiteLLM router
                prompt_template="medical_extract_family_vitals.j2",
                timeout_sec=20.0,
            ),
            ExtractionWave(
                name="validate_and_merge",
                model_role="reasoning",  # Sonnet text-only validator
                prompt_template="medical_extract_validate_merge.j2",
                timeout_sec=20.0,
            ),
        ]

    # ----------------------------------------------------------------------
    # Public entry point
    # ----------------------------------------------------------------------

    async def run(
        self,
        *,
        tenant_id: uuid.UUID,
        patient_id: uuid.UUID,
        pdf_pages_text: str,
        source_document_ids: list[uuid.UUID] | None = None,
    ) -> MedicalHistoryV1:
        """Extract medical history from a patient PDF.

        Parameters
        ----------
        tenant_id
            Required. Filters every persistence + Qdrant collection (R2).
        patient_id
            Required. Joins extracted history to the patient entity.
        pdf_pages_text
            Pre-OCR'd / pre-vision-decoded textual content of the PDF. The
            extractor is text-driven; vision-decoding the PDF to text is
            done UPSTREAM (T-extractors-1 caller). Vision-capable model
            roles still hint at multimodal routing if the upstream wants
            to pass image references — but the canonical contract is text.
        source_document_ids
            Optional list of source document UUIDs (audit trail linkage).

        Returns
        -------
        MedicalHistoryV1
            Always returns a non-None instance. ``confidence_score`` reflects
            extraction quality. ``extraction_warnings`` carries per-wave
            warnings (timeouts, parse failures, etc.).
        """
        run_started = time.monotonic()
        logger.info(
            f"{self.log_prefix}_starting",
            tenant_id=str(tenant_id),
            patient_id=str(patient_id),
            pdf_chars=len(pdf_pages_text),
        )

        # 1-3. Run waves 1-3 in parallel (vision-bound, no inter-wave dep).
        wave_outputs: dict[str, dict[str, Any]] = {}
        wave_costs_usd: dict[str, Decimal] = {}
        wave_warnings: list[str] = []
        wave_confidences: dict[str, float] = {}

        parallel_waves = self._waves[:3]  # W1, W2, W3
        coros = [self._run_one_wave(wave, pdf_pages_text=pdf_pages_text) for wave in parallel_waves]
        results = await asyncio.gather(*coros, return_exceptions=True)

        for wave, result in zip(parallel_waves, results, strict=True):
            if isinstance(result, BaseException):
                logger.warning(
                    f"{self.log_prefix}_wave_failed",
                    wave=wave.name,
                    error_type=type(result).__name__,
                    error_msg=str(result)[:200],
                )
                wave_warnings.append(f"{wave.name}_exception:{type(result).__name__}")
                wave_outputs[wave.name] = {}
                wave_costs_usd[wave.name] = Decimal("0")
                wave_confidences[wave.name] = 0.0
                continue
            wave_outputs[wave.name] = result["parsed"]
            wave_costs_usd[wave.name] = result["cost_usd"]
            wave_confidences[wave.name] = float(result["parsed"].get("wave_confidence", 0.0))
            wave_warnings.extend(result["parsed"].get("wave_warnings", []) or [])

        # 4. Run wave 4 (validate_and_merge) sequentially with W1-W3 outputs.
        validate_wave = self._waves[3]
        try:
            validate_result = await self._run_validate_wave(
                validate_wave,
                wave_1=wave_outputs.get("allergies_and_medications", {}),
                wave_2=wave_outputs.get("conditions_and_surgeries", {}),
                wave_3=wave_outputs.get("family_and_vitals", {}),
            )
            wave_outputs["validate_and_merge"] = validate_result["parsed"]
            wave_costs_usd["validate_and_merge"] = validate_result["cost_usd"]
            wave_confidences["validate_and_merge"] = 1.0  # Validator's own confidence is meta.
            wave_warnings.extend(validate_result["parsed"].get("merged_warnings", []) or [])
        except Exception as exc:  # noqa: BLE001 — defensive, wave failure is partial-result
            logger.warning(
                f"{self.log_prefix}_validate_wave_failed",
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
            )
            wave_outputs["validate_and_merge"] = {}
            wave_costs_usd["validate_and_merge"] = Decimal("0")
            wave_confidences["validate_and_merge"] = 0.0
            wave_warnings.append(f"validate_and_merge_exception:{type(exc).__name__}")

        # 5. Cost budget enforcement (V-AE-16 SSoT).
        total_cost = sum(wave_costs_usd.values(), Decimal("0"))
        if total_cost > self._cost_budget_usd:
            logger.warning(
                f"{self.log_prefix}_cost_budget_exceeded",
                total_cost_usd=str(total_cost),
                budget_usd=str(self._cost_budget_usd),
                tenant_id=str(tenant_id),
                patient_id=str(patient_id),
            )
            wave_warnings.append(f"cost_budget_exceeded:total={total_cost}_USD>{self._cost_budget_usd}")

        # 6. Merge wave outputs into MedicalHistoryV1.
        history = self._merge_outputs(
            wave_outputs=wave_outputs,
            wave_confidences=wave_confidences,
            wave_warnings=wave_warnings,
        )

        duration_ms = int((time.monotonic() - run_started) * 1000)

        # 7. Best-effort persistence + side-effects (each isolated).
        history_id = uuid.uuid4()
        await self._merge_and_save(
            history=history,
            tenant_id=tenant_id,
            patient_id=patient_id,
            history_id=history_id,
            source_document_ids=source_document_ids or [],
            wave_costs_usd=wave_costs_usd,
            duration_ms=duration_ms,
        )

        logger.info(
            f"{self.log_prefix}_complete",
            tenant_id=str(tenant_id),
            patient_id=str(patient_id),
            history_id=str(history_id),
            confidence_score=history.confidence_score,
            total_cost_usd=str(total_cost),
            duration_ms=duration_ms,
            allergies_count=len(history.allergies),
            conditions_count=len(history.chronic_conditions),
            medications_count=len(history.current_medications),
            warnings_count=len(history.extraction_warnings),
        )

        return history

    # ----------------------------------------------------------------------
    # Wave execution helpers
    # ----------------------------------------------------------------------

    def _load_prompt(self, template_name: str) -> str:
        """Load + cache a Jinja2-template-string from disk.

        Templates use ``str.format(...)`` placeholders (NOT real Jinja2 — we
        keep the cache prefix byte-identical and avoid runtime Jinja2 import).
        """
        if template_name in self._prompt_cache:
            return self._prompt_cache[template_name]
        path = _PROMPTS_DIR / template_name
        text = path.read_text(encoding="utf-8")
        self._prompt_cache[template_name] = text
        return text

    async def _run_one_wave(
        self,
        wave: ExtractionWave,
        *,
        pdf_pages_text: str,
    ) -> dict[str, Any]:
        """Execute a single extraction wave + parse + capture cost.

        Returns dict with ``parsed`` (dict from JSON) and ``cost_usd`` (Decimal).
        Raises on timeout or LLM-level error — caller handles via
        ``return_exceptions=True``.
        """
        prompt_template = self._load_prompt(wave.prompt_template)
        # NB: use str.replace (not str.format) — templates carry literal `{`
        # / `}` in the JSON output schema example. Using str.format would
        # interpret them as format specs. Marker style ``{{PDF_PAGES_TEXT}}``
        # is also cache-prefix-friendly: byte-identical across calls until
        # the marker boundary.
        prompt = prompt_template.replace("{{PDF_PAGES_TEXT}}", pdf_pages_text)

        wave_started = time.monotonic()
        try:
            response = await asyncio.wait_for(
                self._llm.ainvoke_text(
                    role=wave.model_role,
                    prompt=prompt,
                    timeout_sec=wave.timeout_sec,
                ),
                timeout=wave.timeout_sec + 2.0,  # asyncio guard around LLM-internal timeout
            )
        except TimeoutError as exc:
            raise TimeoutError(f"wave={wave.name}_timeout_after_{wave.timeout_sec}s") from exc
        wave_duration_ms = int((time.monotonic() - wave_started) * 1000)

        # Capture cost via LiteLLM CustomLogger bridge (PI-12 S1 T-1 cement).
        cost_usd = self._resolve_wave_cost(response, wave_name=wave.name)
        parsed = self._parse_wave_json(response.content, wave_name=wave.name)

        logger.info(
            f"{self.log_prefix}_wave_complete",
            wave=wave.name,
            duration_ms=wave_duration_ms,
            cost_usd=str(cost_usd) if cost_usd is not None else None,
            wave_confidence=parsed.get("wave_confidence"),
        )

        return {"parsed": parsed, "cost_usd": cost_usd or Decimal("0")}

    async def _run_validate_wave(
        self,
        wave: ExtractionWave,
        *,
        wave_1: dict[str, Any],
        wave_2: dict[str, Any],
        wave_3: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the validate_and_merge wave with formatted W1-W3 outputs."""
        prompt_template = self._load_prompt(wave.prompt_template)
        # See _run_one_wave: str.replace (not str.format) — JSON braces are literal.
        prompt = (
            prompt_template.replace("{{WAVE_1_OUTPUT}}", json.dumps(wave_1, ensure_ascii=False))
            .replace("{{WAVE_2_OUTPUT}}", json.dumps(wave_2, ensure_ascii=False))
            .replace("{{WAVE_3_OUTPUT}}", json.dumps(wave_3, ensure_ascii=False))
        )
        try:
            response = await asyncio.wait_for(
                self._llm.ainvoke_text(
                    role=wave.model_role,
                    prompt=prompt,
                    timeout_sec=wave.timeout_sec,
                ),
                timeout=wave.timeout_sec + 2.0,
            )
        except TimeoutError as exc:
            raise TimeoutError(f"wave={wave.name}_timeout_after_{wave.timeout_sec}s") from exc

        cost_usd = self._resolve_wave_cost(response, wave_name=wave.name)
        parsed = self._parse_wave_json(response.content, wave_name=wave.name)

        return {"parsed": parsed, "cost_usd": cost_usd or Decimal("0")}

    @staticmethod
    def _resolve_wave_cost(response: _LLMResponse, *, wave_name: str) -> Decimal | None:
        """Pull cost via LiteLLM CustomLogger bridge.

        Per PI-12 S1 T-1 cement: ``pop_cost(litellm_call_id)`` returns
        ``Decimal | None``. ``None`` means cost-unknown (do NOT default to 0
        — masks cost-tracking drift); we surface a warning + record it as
        a wave warning downstream.
        """
        if response.litellm_call_id is None:
            logger.warning(
                "vitalia_medical_kb_extraction.wave_cost_unknown_no_call_id",
                wave=wave_name,
            )
            return None
        cost = pop_cost(response.litellm_call_id)
        if cost is None:
            logger.warning(
                "vitalia_medical_kb_extraction.wave_cost_unknown",
                wave=wave_name,
                call_id=response.litellm_call_id,
            )
        return cost

    @staticmethod
    def _parse_wave_json(content: str, *, wave_name: str) -> dict[str, Any]:
        """Parse wave LLM output as JSON.

        Tolerant: tries to strip Markdown code fences if model wrapped output
        despite prompt instructions. On final failure, returns empty dict +
        logs warning (caller treats as zero-confidence wave).
        """
        text = content.strip()
        if text.startswith("```"):
            # Strip fenced code block (defensive — prompt forbids markdown but
            # LLMs occasionally ignore).
            lines = text.split("\n")
            if len(lines) >= 2:
                text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as exc:
            logger.warning(
                "vitalia_medical_kb_extraction.wave_json_parse_failed",
                wave=wave_name,
                error=str(exc)[:200],
                content_preview=text[:200],
            )
        return {}

    # ----------------------------------------------------------------------
    # Merge logic (subclass concern)
    # ----------------------------------------------------------------------

    @staticmethod
    def _merge_outputs(
        *,
        wave_outputs: dict[str, dict[str, Any]],
        wave_confidences: dict[str, float],
        wave_warnings: list[str],
    ) -> MedicalHistoryV1:
        """Merge 4-wave outputs into final MedicalHistoryV1 instance.

        Allergy/Condition/Medication/Surgery primitives constructed defensively:
        any malformed entry from the LLM is silently dropped + warning recorded.
        """
        warnings = list(wave_warnings)

        allergies = MedicalKBExtractor._parse_list(
            wave_outputs.get("allergies_and_medications", {}).get("allergies", []),
            Allergy,
            warnings,
            entity_name="allergy",
        )
        medications = MedicalKBExtractor._parse_list(
            wave_outputs.get("allergies_and_medications", {}).get("current_medications", []),
            Medication,
            warnings,
            entity_name="medication",
        )
        conditions = MedicalKBExtractor._parse_list(
            wave_outputs.get("conditions_and_surgeries", {}).get("chronic_conditions", []),
            Condition,
            warnings,
            entity_name="condition",
        )
        surgeries = MedicalKBExtractor._parse_list(
            wave_outputs.get("conditions_and_surgeries", {}).get("past_surgeries", []),
            Surgery,
            warnings,
            entity_name="surgery",
        )

        family_history = MedicalKBExtractor._parse_optional(
            wave_outputs.get("family_and_vitals", {}).get("family_history"),
            FamilyHistorySummary,
            warnings,
            entity_name="family_history",
        )
        vital_signs = MedicalKBExtractor._parse_optional(
            wave_outputs.get("family_and_vitals", {}).get("vital_signs_recent"),
            VitalSigns,
            warnings,
            entity_name="vital_signs",
        )

        # Aggregate confidence: weighted sum + validator adjustment.
        base_confidence = sum(
            wave_confidences.get(name, 0.0) * weight for name, weight in _WAVE_CONFIDENCE_WEIGHTS.items()
        )
        validator_adj = float(wave_outputs.get("validate_and_merge", {}).get("validation_score_adjustment", 0.0) or 0.0)
        # Validator adjustment is bounded [-0.3, 0.0] per prompt.
        validator_adj = max(-0.3, min(0.0, validator_adj))
        confidence = max(0.0, min(1.0, base_confidence + validator_adj))

        missing_required = list(
            wave_outputs.get("validate_and_merge", {}).get("merged_missing_required_fields", []) or []
        )

        return MedicalHistoryV1(
            allergies=allergies,
            chronic_conditions=conditions,
            current_medications=medications,
            past_surgeries=surgeries,
            family_history=family_history,
            vital_signs_recent=vital_signs,
            confidence_score=round(confidence, 3),
            missing_required_fields=missing_required,
            extraction_warnings=warnings,
        )

    @staticmethod
    def _parse_list(
        raw: list[Any],
        cls: type,
        warnings: list[str],
        *,
        entity_name: str,
    ) -> list[Any]:
        """Defensively construct a list of Pydantic instances.

        Drops malformed entries silently; appends a warning per drop.
        """
        result: list[Any] = []
        if not isinstance(raw, list):
            warnings.append(f"{entity_name}_unexpected_type_{type(raw).__name__}")
            return result
        for idx, item in enumerate(raw):
            if not isinstance(item, dict):
                warnings.append(f"{entity_name}_item_{idx}_not_dict")
                continue
            try:
                result.append(cls(**item))
            except Exception as exc:  # noqa: BLE001 — Pydantic ValidationError + edge cases
                warnings.append(f"{entity_name}_item_{idx}_invalid:{type(exc).__name__}")
        return result

    @staticmethod
    def _parse_optional(
        raw: Any,
        cls: type,
        warnings: list[str],
        *,
        entity_name: str,
    ) -> Any:
        """Defensively construct an Optional Pydantic instance."""
        if raw is None:
            return None
        if not isinstance(raw, dict):
            warnings.append(f"{entity_name}_unexpected_type_{type(raw).__name__}")
            return None
        try:
            return cls(**raw)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{entity_name}_invalid:{type(exc).__name__}")
            return None

    # ----------------------------------------------------------------------
    # Persistence + side-effects (subclass concern, best-effort)
    # ----------------------------------------------------------------------

    async def _merge_and_save(
        self,
        *,
        history: MedicalHistoryV1,
        tenant_id: uuid.UUID,
        patient_id: uuid.UUID,
        history_id: uuid.UUID,
        source_document_ids: list[uuid.UUID],
        wave_costs_usd: dict[str, Decimal],
        duration_ms: int,
    ) -> None:
        """Persist the extraction product + run side-effects (all best-effort).

        Order matters:
          1. Persist row (history_repo.save_medical) — primary durable artifact.
          2. Index Qdrant (RAG visibility) — best-effort, isolated try/except.
          3. Outbox event emission — best-effort, isolated try/except.
          4. Audit log — best-effort, isolated try/except.

        Any single side-effect failing MUST NOT raise to the caller.
        """
        # 1. Persistence (sql row).
        try:
            await self._persist_history(
                history=history,
                tenant_id=tenant_id,
                patient_id=patient_id,
                history_id=history_id,
                source_document_ids=source_document_ids,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort persistence
            logger.warning(
                f"{self.log_prefix}_persist_history_failed",
                error_type=type(exc).__name__,
                error_msg=str(exc)[:200],
                tenant_id=str(tenant_id),
                patient_id=str(patient_id),
                history_id=str(history_id),
            )

        # 2. Qdrant indexing (RAG).
        if self._qdrant is not None:
            try:
                # PII sanitisation BEFORE Qdrant write — payload may end up in
                # RAG retrieval contexts surfaced to copilot prompts.
                payload = sanitize_payload(history.model_dump(mode="json"))
                await self._qdrant.index_medical_history(
                    tenant_id=tenant_id,
                    patient_id=patient_id,
                    history_id=history_id,
                    payload=payload,
                )
            except Exception as exc:  # noqa: BLE001 — best-effort RAG index
                logger.warning(
                    f"{self.log_prefix}_qdrant_index_failed",
                    error_type=type(exc).__name__,
                    error_msg=str(exc)[:200],
                    tenant_id=str(tenant_id),
                    history_id=str(history_id),
                )

        # 3. Outbox domain event.
        if self._outbox is not None:
            try:
                event_payload = sanitize_payload(
                    {
                        "history_id": str(history_id),
                        "patient_id": str(patient_id),
                        "extractor_version": EXTRACTOR_VERSION,
                        "schema_version": history.schema_version,
                        "confidence_score": history.confidence_score,
                        "allergies_count": len(history.allergies),
                        "conditions_count": len(history.chronic_conditions),
                        "medications_count": len(history.current_medications),
                        "surgeries_count": len(history.past_surgeries),
                        "warnings_count": len(history.extraction_warnings),
                        "missing_required_count": len(history.missing_required_fields),
                        "duration_ms": duration_ms,
                        "total_cost_usd": str(sum(wave_costs_usd.values(), Decimal("0"))),
                    }
                )
                await self._outbox.publish(
                    event_type="MedicalHistoryExtractedV1",
                    tenant_id=tenant_id,
                    payload=event_payload,
                )
            except Exception as exc:  # noqa: BLE001 — best-effort event emit
                logger.warning(
                    f"{self.log_prefix}_outbox_publish_failed",
                    error_type=type(exc).__name__,
                    error_msg=str(exc)[:200],
                    tenant_id=str(tenant_id),
                    history_id=str(history_id),
                )

        # 4. Audit log (medical_pii_extracted_from_upload).
        if self._audit_log is not None:
            try:
                audit_payload = sanitize_payload(
                    {
                        "history_id": str(history_id),
                        "extractor_version": EXTRACTOR_VERSION,
                        "confidence_score": history.confidence_score,
                        "warnings": list(history.extraction_warnings),
                        "needs_manual_review": history.confidence_score < MIN_ACCEPTABLE_CONFIDENCE,
                    }
                )
                await self._audit_log.log(
                    tenant_id=tenant_id,
                    patient_id=patient_id,
                    event_type="medical_pii_extracted_from_upload",
                    payload=audit_payload,
                )
            except Exception as exc:  # noqa: BLE001 — best-effort audit
                logger.warning(
                    f"{self.log_prefix}_audit_log_failed",
                    error_type=type(exc).__name__,
                    error_msg=str(exc)[:200],
                    tenant_id=str(tenant_id),
                    history_id=str(history_id),
                )

    async def _persist_history(
        self,
        *,
        history: MedicalHistoryV1,
        tenant_id: uuid.UUID,
        patient_id: uuid.UUID,
        history_id: uuid.UUID,
        source_document_ids: list[uuid.UUID],
    ) -> None:
        """Persist via repo. Lazy-import ORM model to avoid hard SQLAlchemy
        coupling when the test injects a fake repo that ignores the model."""
        from datetime import datetime, timezone

        try:
            from src.modules.vitalia.infrastructure.models.medical_history_model import (
                VitaliaPatientMedicalHistoryModel,
            )

            row = VitaliaPatientMedicalHistoryModel(
                id=history_id,
                tenant_id=tenant_id,
                patient_id=patient_id,
                extraction_confidence=Decimal(str(history.confidence_score)),
                extracted_payload=history.model_dump(mode="json"),
                extractor_version=EXTRACTOR_VERSION,
                last_extracted_at=datetime.now(timezone.utc),
                source_document_ids=[str(sid) for sid in source_document_ids],
            )
        except Exception as exc:  # noqa: BLE001 — defensive against import-only test fakes
            logger.warning(
                f"{self.log_prefix}_orm_model_unavailable_using_dict",
                error_type=type(exc).__name__,
            )
            row = {  # type: ignore[assignment]
                "id": history_id,
                "tenant_id": tenant_id,
                "patient_id": patient_id,
                "extraction_confidence": Decimal(str(history.confidence_score)),
                "extracted_payload": history.model_dump(mode="json"),
                "extractor_version": EXTRACTOR_VERSION,
                "source_document_ids": [str(sid) for sid in source_document_ids],
            }

        await self._history_repo.save_medical(row)


__all__ = [
    "DEFAULT_COST_BUDGET_USD",
    "EXTRACTOR_VERSION",
    "MIN_ACCEPTABLE_CONFIDENCE",
    "MedicalKBExtractor",
]
