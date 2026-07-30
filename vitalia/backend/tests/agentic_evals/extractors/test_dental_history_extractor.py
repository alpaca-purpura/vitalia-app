"""Vitalia AGENTIC extractor tests — `DentalHistoryExtractor` (R23 Opus 4.7).

Story 11 T-extractors-2.

Spec sources:
  * 02-design-agentic.md § 7.2 — DentalHistoryV1 + 4 vision-heavy waves
  * 03-arch-agentic.md § 5.2 — class skeleton + inheritance gate § 5.3
  * 06-tickets.yaml::T-extractors-2 acceptance A1 (FDI notation) + A2 (cost ≤$0.18)
  * 04-validators.yaml V-AE-6 + V-AE-16

TDD: RED first per `.claude/rules/tdd-mandatory.md`.

Test inventory (10 tests):
  T1 test_inherits_base_extraction_orchestrator     — § 5.3 arch fitness gate (subclass)
  T2 test_4_wave_pipeline_definition                — § 7.2 wave names + roles
  T3 test_fdi_notation                              — A1 acceptance: missing_pieces validates FDI 11-48
  T4 test_cost_budget                               — A2 acceptance: ≤$0.18 USD per PDF (vision-heavy)
  T5 test_dental_history_v1_schema_shape            — § 7.2 output fields + confidence_score [0,1]
  T6 test_run_emits_dental_chart_ready_event        — § 7.2 side-effect — DentalChartReadyV1 → Aurora
  T7 test_run_persists_dental_history               — § 7.2 side-effect — VitaliaPatientDentalHistoryModel row
  T8 test_pii_sanitized_in_observability            — `tenant-isolation` + `pii-sanitisation`
  T9 test_tenant_isolation_per_qdrant_collection    — § 7.2 tenant-scoped collection name
  T10 test_wave_timeout_degrades_confidence         — § 7.2 error mode: degraded confidence + warning

Anti-patterns prohibidos (auditor C2 enforce):
  * NO mirror BaseExtractionOrchestrator — extends shared (anti-duplication.md)
  * NO hardcoded wire model names in waves — uses ModelRole enum (LLM_ROLE_BY_SITE SSoT)
  * NO bypass of sanitize_payload before observability writes (PII)
  * NO infinite-loop graphs — wave count fixed at class scope
  * NO tenant_id mid-prompt-block (cache-prefix invariant)
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# T1 — Inherits BaseExtractionOrchestrator (arch fitness § 5.3)
# ─────────────────────────────────────────────────────────────────────────────


def test_inherits_base_extraction_orchestrator() -> None:
    """A1 acceptance + § 5.3 arch fitness: DentalHistoryExtractor MUST extend
    luana_core_extraction.base_orchestrator.BaseExtractionOrchestrator."""
    from luana_core_extraction.base_orchestrator import BaseExtractionOrchestrator

    from src.modules.vitalia.copilot.extractors.dental_history_extractor import (
        DentalHistoryExtractor,
    )

    assert issubclass(DentalHistoryExtractor, BaseExtractionOrchestrator), (
        "DentalHistoryExtractor MUST inherit from BaseExtractionOrchestrator "
        "(anti-duplication.md SSoT row + 03-arch § 5.3 arch fitness gate). "
        "Wave scheduling + progress emission must come from the shared base, "
        "never duplicated."
    )


# ─────────────────────────────────────────────────────────────────────────────
# T2 — 4-wave pipeline definition (§ 7.2)
# ─────────────────────────────────────────────────────────────────────────────


def test_4_wave_pipeline_definition() -> None:
    """§ 7.2: 4 waves declared at class scope (vision-heavy)."""
    from src.modules.vitalia.copilot.extractors.dental_history_extractor import (
        DentalHistoryExtractor,
    )

    waves = DentalHistoryExtractor.waves
    assert len(waves) == 4, f"Expected 4 waves per § 7.2, got {len(waves)}"

    expected_names = [
        "missing_pieces_chart",
        "restorations_and_periodontal",
        "bite_and_radiographs",
        "validate_and_merge",
    ]
    actual_names = [w.name for w in waves]
    assert actual_names == expected_names, (
        f"Wave order/names diverge from § 7.2 spec: {actual_names} != {expected_names}"
    )

    # First 3 waves are vision-bearing — model_role uses 'vision' role.
    # Final merge wave uses reasoning role.
    assert waves[0].model_role == "vision"
    assert waves[1].model_role == "vision"
    assert waves[2].model_role == "vision"  # Haiku vision per § 7.2
    assert waves[3].model_role == "reasoning"

    # Each wave declares a Jinja prompt template
    for w in waves:
        assert w.prompt_template.endswith(".j2"), f"Wave {w.name} missing .j2 prompt"
        assert w.prompt_template.startswith("dental_extract_"), (
            f"Wave {w.name} prompt name must follow dental_extract_*.j2 convention"
        )


# ─────────────────────────────────────────────────────────────────────────────
# T3 — A1 acceptance: FDI notation validation
# ─────────────────────────────────────────────────────────────────────────────


def test_fdi_notation() -> None:
    """A1 acceptance: missing_pieces parsed as FDI notation (11-48 range).

    FDI World Dental Federation universal numbering system:
      Quadrants 1-4 (adult permanent):
        1 = upper right    teeth 11-18
        2 = upper left     teeth 21-28
        3 = lower left     teeth 31-38
        4 = lower right    teeth 41-48
      Tooth position: quadrant_digit * 10 + position (1-8 from midline)

    Valid: 11..18, 21..28, 31..38, 41..48.
    Invalid: 19, 20, 29..30, 39..40, 49+, 0, 10, 100, negative.
    """
    from src.modules.vitalia.copilot.extractors._schemas import (
        DentalHistoryV1,
        ToothPosition,
    )

    # ── Valid FDI codes accepted ──
    for code in [11, 18, 21, 28, 31, 38, 41, 48]:
        tp = ToothPosition(fdi_code=code)
        assert tp.fdi_code == code

    # ── Invalid FDI codes rejected by Pydantic validation ──
    from pydantic import ValidationError

    for invalid in [10, 19, 20, 29, 30, 39, 40, 49, 50, 99, 0, -1, 100]:
        with pytest.raises(ValidationError):
            ToothPosition(fdi_code=invalid)

    # ── DentalHistoryV1 with missing_pieces from extractor wave ──
    history = DentalHistoryV1(
        missing_pieces=[ToothPosition(fdi_code=18), ToothPosition(fdi_code=48)],
        confidence_score=0.85,
    )
    assert len(history.missing_pieces) == 2
    assert {p.fdi_code for p in history.missing_pieces} == {18, 48}


# ─────────────────────────────────────────────────────────────────────────────
# T4 — A2 acceptance: Cost budget ≤$0.18 USD per PDF (vision-heavy)
# ─────────────────────────────────────────────────────────────────────────────


def test_cost_budget() -> None:
    """A2 acceptance + V-AE-16 threshold: cost per PDF ≤$0.18 USD.

    Synthetic per-wave usage data → aggregate cost ≤ ceiling.
    Dental ceiling = $0.18 (vision-heavy bar) > medical ceiling = $0.15.
    """
    from src.modules.vitalia.copilot.extractors.dental_history_extractor import (
        COST_CEILING_USD_PER_PDF,
        DentalHistoryExtractor,
    )

    # Spec V-AE-16: cost_usd_max_per_pdf_dental: 0.18
    assert COST_CEILING_USD_PER_PDF == 0.18, f"Cost ceiling drift from V-AE-16 threshold: {COST_CEILING_USD_PER_PDF}"

    # Synthetic usage per wave (vision tokens are pricier than text tokens).
    # These are illustrative cents accounting; real costs come from
    # CostRecorder.calculate_cost(model, usage). The test verifies the
    # extractor's _aggregate_cost helper sums correctly and stays within budget.
    wave_usages = [
        {"input_tokens": 4_000, "output_tokens": 800, "wave_cost_usd": 0.045},  # missing_pieces_chart vision
        {"input_tokens": 4_000, "output_tokens": 800, "wave_cost_usd": 0.050},  # restorations_periodontal vision
        {"input_tokens": 3_000, "output_tokens": 500, "wave_cost_usd": 0.030},  # bite_radiographs Haiku vision
        {"input_tokens": 2_000, "output_tokens": 400, "wave_cost_usd": 0.015},  # validate_merge reasoning
    ]
    total = DentalHistoryExtractor._aggregate_cost(wave_usages)
    assert total <= COST_CEILING_USD_PER_PDF, (
        f"Synthetic 4-wave cost {total:.4f} exceeds dental ceiling "
        f"{COST_CEILING_USD_PER_PDF:.2f} (V-AE-16). Tune wave model selection."
    )

    # Edge: a hostile PDF that pushes cost above ceiling MUST be flagged by the
    # cost guard (warning + degraded confidence — not silent budget overrun).
    hostile_usages = [
        {"input_tokens": 8_000, "output_tokens": 1_500, "wave_cost_usd": 0.08},
        {"input_tokens": 8_000, "output_tokens": 1_500, "wave_cost_usd": 0.08},
        {"input_tokens": 5_000, "output_tokens": 900, "wave_cost_usd": 0.05},
        {"input_tokens": 3_000, "output_tokens": 600, "wave_cost_usd": 0.025},
    ]
    over_total = DentalHistoryExtractor._aggregate_cost(hostile_usages)
    assert over_total > COST_CEILING_USD_PER_PDF
    # The extractor MUST be able to detect the overrun — symmetric API.
    assert DentalHistoryExtractor._cost_overrun(over_total) is True
    assert DentalHistoryExtractor._cost_overrun(total) is False


# ─────────────────────────────────────────────────────────────────────────────
# T5 — DentalHistoryV1 schema shape (§ 7.2 fields)
# ─────────────────────────────────────────────────────────────────────────────


def test_dental_history_v1_schema_shape() -> None:
    """§ 7.2: DentalHistoryV1 contains the 5 dental fields + confidence + warnings."""
    from src.modules.vitalia.copilot.extractors._schemas import DentalHistoryV1

    fields = DentalHistoryV1.model_fields
    expected = {
        "schema_version",
        "missing_pieces",
        "existing_restorations",
        "periodontal_status",
        "bite_alignment",
        "radiographs_referenced",
        "confidence_score",
        "missing_required_fields",
        "extraction_warnings",
    }
    assert expected.issubset(fields.keys()), f"Missing fields in DentalHistoryV1: {expected - fields.keys()}"

    # confidence_score range [0, 1]
    from pydantic import ValidationError

    DentalHistoryV1(confidence_score=0.0)  # boundary lower
    DentalHistoryV1(confidence_score=1.0)  # boundary upper
    with pytest.raises(ValidationError):
        DentalHistoryV1(confidence_score=1.5)  # over upper
    with pytest.raises(ValidationError):
        DentalHistoryV1(confidence_score=-0.1)  # under lower

    # schema_version cement (Story D playbook — never mutate V1)
    h = DentalHistoryV1()
    assert h.schema_version == 1


# ─────────────────────────────────────────────────────────────────────────────
# T6 — run() emits DentalChartReadyV1 event (§ 7.2 side-effect)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_emits_dental_chart_ready_event() -> None:
    """§ 7.2 side-effect: emits DentalChartReadyV1 consumed by Aurora's
    TreatmentFollowupWorkflow for implant procedure planning."""

    captured_events: list[Any] = []

    class FakeEventBus:
        async def publish(self, event: Any) -> None:
            captured_events.append(event)

    extractor = _build_extractor_with_fakes(event_bus=FakeEventBus())
    tenant_id = uuid4()
    patient_id = uuid4()

    await extractor.run(
        pdf_url="https://signed.example/doc.pdf",
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    # Must publish exactly one event of type DentalChartReadyV1
    assert len(captured_events) == 1, f"Expected 1 event, got {len(captured_events)}"
    evt = captured_events[0]
    assert type(evt).__name__ == "DentalChartReadyV1"
    # Event MUST carry tenant + patient ids for Aurora consumer
    assert getattr(evt, "tenant_id", None) == tenant_id
    assert getattr(evt, "patient_id", None) == patient_id


# ─────────────────────────────────────────────────────────────────────────────
# T7 — run() persists VitaliaPatientDentalHistoryModel row (§ 7.2 side-effect)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_persists_dental_history() -> None:
    """§ 7.2 side-effect: persist patient_dental_histories row (tenant-isolated)."""

    persisted_rows: list[dict[str, Any]] = []

    class FakeRepo:
        async def upsert(self, *, tenant_id: UUID, patient_id: UUID, payload: dict) -> None:
            persisted_rows.append(
                {
                    "tenant_id": tenant_id,
                    "patient_id": patient_id,
                    "payload": payload,
                }
            )

    extractor = _build_extractor_with_fakes(history_repo=FakeRepo())
    tenant_id = uuid4()
    patient_id = uuid4()

    await extractor.run(
        pdf_url="https://signed.example/doc.pdf",
        tenant_id=tenant_id,
        patient_id=patient_id,
    )

    assert len(persisted_rows) == 1
    row = persisted_rows[0]
    assert row["tenant_id"] == tenant_id
    assert row["patient_id"] == patient_id
    payload = row["payload"]
    # DentalHistoryV1 fields landed in payload
    assert "missing_pieces" in payload
    assert "confidence_score" in payload
    assert "schema_version" in payload


# ─────────────────────────────────────────────────────────────────────────────
# T8 — PII sanitization before observability writes
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pii_sanitized_in_observability() -> None:
    """PII (DNI/email/phone in PDF) MUST be sanitized via sanitize_payload
    before reaching trace_event_repo. Per `.tessl/...pii-sanitisation` +
    copilot-observability rule + spec § 7.2 PII heavy error mode."""

    captured_traces: list[dict[str, Any]] = []

    class FakeTraceRepo:
        async def record(self, *, tenant_id: UUID, event_type: str, payload: dict, **kw: Any) -> None:
            captured_traces.append({"event_type": event_type, "payload": payload})

    # Wave outputs include simulated PII the extractor accidentally surfaces.
    # The extractor MUST scrub via sanitize_payload before passing to the recorder.
    pii_laden_wave_outputs = {
        "missing_pieces_chart": {
            "missing": [18, 48],
            "patient_dni": "12345678",  # raw DNI — must be scrubbed
            "patient_email": "ana@example.com",  # raw email — must be scrubbed
        },
    }

    extractor = _build_extractor_with_fakes(
        trace_event_repo=FakeTraceRepo(),
        pii_laden_wave_outputs=pii_laden_wave_outputs,
    )

    await extractor.run(
        pdf_url="https://signed.example/doc.pdf",
        tenant_id=uuid4(),
        patient_id=uuid4(),
    )

    # At least one trace event captured
    assert len(captured_traces) >= 1
    # Walk every payload string field — raw DNI / email must NEVER appear.
    for trace in captured_traces:
        flat = str(trace["payload"])
        assert "12345678" not in flat, "Raw DNI leaked into trace payload"
        assert "ana@example.com" not in flat, "Raw email leaked into trace payload"


# ─────────────────────────────────────────────────────────────────────────────
# T9 — Tenant isolation: per-tenant Qdrant collection
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tenant_isolation_per_qdrant_collection() -> None:
    """Per spec § 7.2 + tenant-isolation rule: index tied to per-tenant Qdrant
    collection — collection name MUST embed tenant_id (NEVER cross-tenant)."""

    indexed_collections: list[str] = []

    class FakeQdrantIndexer:
        async def index(self, *, collection: str, payload: dict, vector: list[float] | None = None) -> None:
            indexed_collections.append(collection)

    extractor = _build_extractor_with_fakes(qdrant_indexer=FakeQdrantIndexer())
    tenant_a = uuid4()
    await extractor.run(
        pdf_url="https://signed.example/doc.pdf",
        tenant_id=tenant_a,
        patient_id=uuid4(),
    )

    assert len(indexed_collections) >= 1
    # Collection name MUST contain the tenant_id — so cross-tenant searches cannot leak.
    assert all(str(tenant_a) in name for name in indexed_collections), (
        f"Qdrant collection name does not embed tenant_id={tenant_a}: {indexed_collections}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# T10 — Wave timeout degrades confidence + records warning (§ 7.2 error mode)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_wave_timeout_degrades_confidence() -> None:
    """§ 7.2 error mode: wave timeout → confidence decremented + warning recorded.
    Pattern from tessl__graceful-degradation: every external call has timeout +
    fallback (degrade gracefully, never crash the extractor)."""

    extractor = _build_extractor_with_fakes(simulate_wave_timeout="bite_and_radiographs")

    persisted: list[dict[str, Any]] = []

    class CapturingRepo:
        async def upsert(self, *, tenant_id: UUID, patient_id: UUID, payload: dict) -> None:
            persisted.append(payload)

    # Re-wire repo
    extractor._history_repo = CapturingRepo()

    await extractor.run(
        pdf_url="https://signed.example/doc.pdf",
        tenant_id=uuid4(),
        patient_id=uuid4(),
    )

    assert len(persisted) == 1
    payload = persisted[0]
    # Confidence MUST be < 1.0 due to wave timeout
    assert payload["confidence_score"] < 1.0
    # Warnings MUST mention the timed-out wave
    warnings = payload.get("extraction_warnings") or []
    assert any("bite_and_radiographs" in str(w) for w in warnings), (
        f"Expected timeout warning for 'bite_and_radiographs' in {warnings}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# Test fixture builder — assemble extractor with fake collaborators.
# ═════════════════════════════════════════════════════════════════════════════


def _build_extractor_with_fakes(
    *,
    event_bus: Any = None,
    history_repo: Any = None,
    trace_event_repo: Any = None,
    qdrant_indexer: Any = None,
    pii_laden_wave_outputs: dict[str, Any] | None = None,
    simulate_wave_timeout: str | None = None,
) -> Any:
    """Construct DentalHistoryExtractor with fake LLM + collaborators.

    Default fakes return minimal valid DentalHistoryV1 payloads per wave.
    Tests override only the collaborator they exercise (DI pattern).
    """
    from src.modules.vitalia.copilot.extractors.dental_history_extractor import (
        DentalHistoryExtractor,
    )

    # ── Default no-op fakes when test does not override ──
    if event_bus is None:
        event_bus = AsyncMock()
        event_bus.publish = AsyncMock(return_value=None)
    if history_repo is None:
        history_repo = AsyncMock()
        history_repo.upsert = AsyncMock(return_value=None)
    if trace_event_repo is None:
        trace_event_repo = AsyncMock()
        trace_event_repo.record = AsyncMock(return_value=None)
    if qdrant_indexer is None:
        qdrant_indexer = AsyncMock()
        qdrant_indexer.index = AsyncMock(return_value=None)

    # ── Fake LLM service that returns canned wave outputs ──
    class FakeLLM:
        async def acomplete(
            self,
            *,
            role: str,
            messages: list[dict[str, Any]],
            timeout_sec: float,
            wave_name: str = "",
            **_kw: Any,
        ) -> dict[str, Any]:
            # Simulate wave timeout — raises asyncio.TimeoutError
            if simulate_wave_timeout and wave_name == simulate_wave_timeout:
                raise asyncio.TimeoutError(f"wave {wave_name} exceeded {timeout_sec}s")

            if pii_laden_wave_outputs and wave_name in pii_laden_wave_outputs:
                content = pii_laden_wave_outputs[wave_name]
            elif wave_name == "missing_pieces_chart":
                content = {"missing": [18, 28]}
            elif wave_name == "restorations_and_periodontal":
                content = {
                    "restorations": [{"tooth_fdi": 36, "type": "crown", "material": "porcelana"}],
                    "periodontal": {"general_status": "leve", "bleeding_index": 0.1},
                }
            elif wave_name == "bite_and_radiographs":
                content = {
                    "bite": {"alignment": "normal", "notes": ""},
                    "radiographs": [{"type": "panoramica", "date_iso": "2026-04-01"}],
                }
            elif wave_name == "validate_and_merge":
                content = {"merge_ok": True, "warnings": []}
            else:
                content = {}

            # Synthetic usage data — keeps cost in budget under happy path
            return {
                "content": content,
                "usage": {"input_tokens": 3_000, "output_tokens": 500},
                "wave_cost_usd": 0.04,
            }

    extractor = DentalHistoryExtractor(
        llm_service=FakeLLM(),
        history_repo=history_repo,
        event_bus=event_bus,
        trace_event_repo=trace_event_repo,
        qdrant_indexer=qdrant_indexer,
    )
    return extractor


__all__: list[str] = []
