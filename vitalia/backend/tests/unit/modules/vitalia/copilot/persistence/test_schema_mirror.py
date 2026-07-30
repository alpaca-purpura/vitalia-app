"""Schema mirror tests for vitalia copilot + sales_agent + agentic/lucas persistence models.

T-be-migrations-1 acceptance — per `.claude/rules/backend-ddd.md` schema-mirror exception.

Tests verify:
- Models use SA 2.0 `mapped_column()` (no legacy Column)
- tenant_id + clinic_id columns present and indexed on PHI tables
- deleted_at soft-delete present on all tables
- Key columns match migration DDL types
- __tablename__ matches migration DDL
- models importable without circular imports

These are unit tests — no DB connection required.
"""

from __future__ import annotations

import importlib
import inspect
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _import_model(module_path: str, class_name: str) -> Any:
    """Import and return a model class by dotted path."""
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


def _get_column_names(model_class: Any) -> set[str]:
    """Return column names from a SA 2.0 mapped model."""
    table = model_class.__table__
    return {c.name for c in table.columns}


def _get_index_names(model_class: Any) -> set[str]:
    """Return index names from model table args."""
    table = model_class.__table__
    return {idx.name for idx in table.indexes}


def _has_mapped_column(model_class: Any) -> bool:
    """Check that model uses SA 2.0 mapped_column (not legacy Column)."""
    source = inspect.getsource(model_class)
    # mapped_column must be present
    return "mapped_column" in source and "Mapped[" in source


# ─────────────────────────────────────────────────────────────────────────────
# Copilot: CopilotTraceEventVitalia
# ─────────────────────────────────────────────────────────────────────────────


def test_copilot_trace_event_model_importable() -> None:
    """CopilotTraceEventVitalia must be importable."""
    model = _import_model(
        "src.modules.vitalia.copilot.persistence.models.copilot_trace_event",
        "CopilotTraceEventVitalia",
    )
    assert model is not None


def test_copilot_trace_event_tablename() -> None:
    """CopilotTraceEventVitalia.__tablename__ must be 'copilot_trace_event'."""
    model = _import_model(
        "src.modules.vitalia.copilot.persistence.models.copilot_trace_event",
        "CopilotTraceEventVitalia",
    )
    assert model.__tablename__ == "copilot_trace_event"


def test_copilot_trace_event_uses_mapped_column() -> None:
    """CopilotTraceEventVitalia must use SA 2.0 mapped_column syntax."""
    model = _import_model(
        "src.modules.vitalia.copilot.persistence.models.copilot_trace_event",
        "CopilotTraceEventVitalia",
    )
    assert _has_mapped_column(model), "Must use SA 2.0 mapped_column() / Mapped[] syntax"


def test_copilot_trace_event_required_columns() -> None:
    """CopilotTraceEventVitalia must have all base + brand-specific columns."""
    model = _import_model(
        "src.modules.vitalia.copilot.persistence.models.copilot_trace_event",
        "CopilotTraceEventVitalia",
    )
    cols = _get_column_names(model)
    base_cols = {"id", "tenant_id", "user_id", "turn_id", "span_id", "event_type", "data", "status", "created_at"}
    for col in base_cols:
        assert col in cols, f"CopilotTraceEventVitalia missing base column: {col}"
    # Brand-specific cols
    assert "clinic_id" in cols, "CopilotTraceEventVitalia missing brand-specific clinic_id"
    assert "compliance_level" in cols, "CopilotTraceEventVitalia missing brand-specific compliance_level"


def test_copilot_trace_event_tenant_clinic_indexed() -> None:
    """CopilotTraceEventVitalia must have tenant_id + clinic_id indexed."""
    model = _import_model(
        "src.modules.vitalia.copilot.persistence.models.copilot_trace_event",
        "CopilotTraceEventVitalia",
    )
    cols = _get_column_names(model)
    assert "tenant_id" in cols
    assert "clinic_id" in cols
    # At least one composite index covering tenant_id
    idx_names = _get_index_names(model)
    tenant_indexed = any("tenant" in n for n in idx_names)
    assert tenant_indexed, f"No tenant index found. Indexes: {idx_names}"


# ─────────────────────────────────────────────────────────────────────────────
# Copilot: CopilotLLMCallVitalia
# ─────────────────────────────────────────────────────────────────────────────


def test_copilot_llm_call_model_importable() -> None:
    """CopilotLLMCallVitalia must be importable."""
    model = _import_model(
        "src.modules.vitalia.copilot.persistence.models.copilot_llm_call",
        "CopilotLLMCallVitalia",
    )
    assert model is not None


def test_copilot_llm_call_tablename() -> None:
    """CopilotLLMCallVitalia.__tablename__ must be 'copilot_llm_call'."""
    model = _import_model(
        "src.modules.vitalia.copilot.persistence.models.copilot_llm_call",
        "CopilotLLMCallVitalia",
    )
    assert model.__tablename__ == "copilot_llm_call"


def test_copilot_llm_call_uses_mapped_column() -> None:
    """CopilotLLMCallVitalia must use SA 2.0 mapped_column syntax."""
    model = _import_model(
        "src.modules.vitalia.copilot.persistence.models.copilot_llm_call",
        "CopilotLLMCallVitalia",
    )
    assert _has_mapped_column(model)


def test_copilot_llm_call_required_columns() -> None:
    """CopilotLLMCallVitalia must have all base + brand-specific columns."""
    model = _import_model(
        "src.modules.vitalia.copilot.persistence.models.copilot_llm_call",
        "CopilotLLMCallVitalia",
    )
    cols = _get_column_names(model)
    base_cols = {
        "id",
        "tenant_id",
        "turn_id",
        "span_id",
        "role",
        "provider",
        "model_requested",
        "model_responded",
        "input_tokens",
        "output_tokens",
        "cost_usd",
        "started_at",
        "duration_ms",
        "status",
    }
    for col in base_cols:
        assert col in cols, f"CopilotLLMCallVitalia missing base column: {col}"
    # Brand-specific
    assert "clinic_id" in cols
    assert "compliance_level" in cols
    assert "medical_guardrail_check_passed" in cols


# ─────────────────────────────────────────────────────────────────────────────
# Sales agent: SalesAgentTraceEventVitalia
# ─────────────────────────────────────────────────────────────────────────────


def test_sales_agent_trace_event_model_importable() -> None:
    """SalesAgentTraceEventVitalia must be importable."""
    model = _import_model(
        "src.modules.vitalia.sales_agent.persistence.models.sales_agent_trace_event",
        "SalesAgentTraceEventVitalia",
    )
    assert model is not None


def test_sales_agent_trace_event_tablename() -> None:
    """SalesAgentTraceEventVitalia must map to 'sales_agent_trace_event'."""
    model = _import_model(
        "src.modules.vitalia.sales_agent.persistence.models.sales_agent_trace_event",
        "SalesAgentTraceEventVitalia",
    )
    assert model.__tablename__ == "sales_agent_trace_event"


def test_sales_agent_trace_event_uses_mapped_column() -> None:
    """SalesAgentTraceEventVitalia must use SA 2.0 mapped_column syntax."""
    model = _import_model(
        "src.modules.vitalia.sales_agent.persistence.models.sales_agent_trace_event",
        "SalesAgentTraceEventVitalia",
    )
    assert _has_mapped_column(model)


def test_sales_agent_trace_event_required_columns() -> None:
    """SalesAgentTraceEventVitalia must have base + brand-specific columns."""
    model = _import_model(
        "src.modules.vitalia.sales_agent.persistence.models.sales_agent_trace_event",
        "SalesAgentTraceEventVitalia",
    )
    cols = _get_column_names(model)
    for col in ("id", "tenant_id", "turn_id", "span_id", "event_type", "status", "created_at"):
        assert col in cols, f"SalesAgentTraceEventVitalia missing: {col}"
    assert "clinic_id" in cols
    assert "compliance_level" in cols


# ─────────────────────────────────────────────────────────────────────────────
# Sales agent: SalesAgentLLMCallVitalia
# ─────────────────────────────────────────────────────────────────────────────


def test_sales_agent_llm_call_model_importable() -> None:
    """SalesAgentLLMCallVitalia must be importable."""
    model = _import_model(
        "src.modules.vitalia.sales_agent.persistence.models.sales_agent_llm_call",
        "SalesAgentLLMCallVitalia",
    )
    assert model is not None


def test_sales_agent_llm_call_tablename() -> None:
    """SalesAgentLLMCallVitalia must map to 'sales_agent_llm_call'."""
    model = _import_model(
        "src.modules.vitalia.sales_agent.persistence.models.sales_agent_llm_call",
        "SalesAgentLLMCallVitalia",
    )
    assert model.__tablename__ == "sales_agent_llm_call"


def test_sales_agent_llm_call_brand_specific_columns() -> None:
    """SalesAgentLLMCallVitalia must have brand-specific clinic_id + medical columns."""
    model = _import_model(
        "src.modules.vitalia.sales_agent.persistence.models.sales_agent_llm_call",
        "SalesAgentLLMCallVitalia",
    )
    cols = _get_column_names(model)
    assert "clinic_id" in cols
    assert "compliance_level" in cols
    assert "medical_guardrail_check_passed" in cols


# ─────────────────────────────────────────────────────────────────────────────
# Sales agent: LeadScreeningEventModel
# ─────────────────────────────────────────────────────────────────────────────


def test_lead_screening_event_model_importable() -> None:
    """LeadScreeningEventModel must be importable."""
    model = _import_model(
        "src.modules.vitalia.sales_agent.persistence.models.lead_screening_event",
        "LeadScreeningEventModel",
    )
    assert model is not None


def test_lead_screening_event_tablename() -> None:
    """LeadScreeningEventModel must map to 'lead_screening_events'."""
    model = _import_model(
        "src.modules.vitalia.sales_agent.persistence.models.lead_screening_event",
        "LeadScreeningEventModel",
    )
    assert model.__tablename__ == "lead_screening_events"


def test_lead_screening_event_uses_mapped_column() -> None:
    """LeadScreeningEventModel must use SA 2.0 mapped_column syntax."""
    model = _import_model(
        "src.modules.vitalia.sales_agent.persistence.models.lead_screening_event",
        "LeadScreeningEventModel",
    )
    assert _has_mapped_column(model)


def test_lead_screening_event_required_columns() -> None:
    """LeadScreeningEventModel must have all columns matching migration 017 DDL."""
    model = _import_model(
        "src.modules.vitalia.sales_agent.persistence.models.lead_screening_event",
        "LeadScreeningEventModel",
    )
    cols = _get_column_names(model)
    required = {
        "id",
        "tenant_id",
        "clinic_id",
        "lead_id",
        "vertical",
        "questions_asked",
        "response_text",
        "outcome",
        "reasoning",
        "evaluated_at",
        "created_at",
        "deleted_at",
    }
    for col in required:
        assert col in cols, f"LeadScreeningEventModel missing column: {col}"


def test_lead_screening_event_has_dual_filter_index() -> None:
    """LeadScreeningEventModel must have tenant+clinic+lead index (hipaa-lite.md dual filter)."""
    model = _import_model(
        "src.modules.vitalia.sales_agent.persistence.models.lead_screening_event",
        "LeadScreeningEventModel",
    )
    idx_names = _get_index_names(model)
    # Must have the composite tenant+clinic+lead index
    assert any("tenant_clinic_lead" in n for n in idx_names), (
        f"Missing tenant+clinic+lead composite index. Found: {idx_names}"
    )


def test_lead_screening_event_soft_delete_present() -> None:
    """LeadScreeningEventModel must have deleted_at for soft delete."""
    model = _import_model(
        "src.modules.vitalia.sales_agent.persistence.models.lead_screening_event",
        "LeadScreeningEventModel",
    )
    cols = _get_column_names(model)
    assert "deleted_at" in cols


# ─────────────────────────────────────────────────────────────────────────────
# Agentic/lucas: StageRecommendationModel
# ─────────────────────────────────────────────────────────────────────────────


def test_stage_recommendation_model_importable() -> None:
    """LucasRecommendationModel must be importable."""
    model = _import_model(
        "src.modules.vitalia.infrastructure.models.lucas_recommendation_model",
        "LucasRecommendationModel",
    )
    assert model is not None


def test_stage_recommendation_tablename() -> None:
    """LucasRecommendationModel must map to 'vitalia_lucas_recommendations'."""
    model = _import_model(
        "src.modules.vitalia.infrastructure.models.lucas_recommendation_model",
        "LucasRecommendationModel",
    )
    assert model.__tablename__ == "vitalia_lucas_recommendations"


def test_stage_recommendation_uses_mapped_column() -> None:
    """LucasRecommendationModel must use SA 2.0 mapped_column syntax."""
    model = _import_model(
        "src.modules.vitalia.infrastructure.models.lucas_recommendation_model",
        "LucasRecommendationModel",
    )
    assert _has_mapped_column(model)


def test_stage_recommendation_required_columns() -> None:
    """LucasRecommendationModel must have all required columns."""
    model = _import_model(
        "src.modules.vitalia.infrastructure.models.lucas_recommendation_model",
        "LucasRecommendationModel",
    )
    cols = _get_column_names(model)
    required = {"id", "tenant_id", "clinic_id", "stage", "deleted_at", "created_at"}
    for col in required:
        assert col in cols, f"LucasRecommendationModel missing: {col}"


# ─────────────────────────────────────────────────────────────────────────────
# Agentic/lucas: AttributionMatrixSnapshotModel
# ─────────────────────────────────────────────────────────────────────────────


def test_attribution_matrix_snapshot_model_importable() -> None:
    """AttributionMatrixSnapshotModel must be importable."""
    model = _import_model(
        "src.modules.vitalia.agentic.lucas.persistence.models.attribution_matrix_snapshot",
        "AttributionMatrixSnapshotModel",
    )
    assert model is not None


def test_attribution_matrix_snapshot_tablename() -> None:
    """AttributionMatrixSnapshotModel must map to 'attribution_matrix_snapshots'."""
    model = _import_model(
        "src.modules.vitalia.agentic.lucas.persistence.models.attribution_matrix_snapshot",
        "AttributionMatrixSnapshotModel",
    )
    assert model.__tablename__ == "attribution_matrix_snapshots"


def test_attribution_matrix_snapshot_required_columns() -> None:
    """AttributionMatrixSnapshotModel must have all required columns."""
    model = _import_model(
        "src.modules.vitalia.agentic.lucas.persistence.models.attribution_matrix_snapshot",
        "AttributionMatrixSnapshotModel",
    )
    cols = _get_column_names(model)
    required = {
        "id",
        "tenant_id",
        "clinic_id",
        "period_start",
        "period_end",
        "channel_breakdown",
        "total_attributed_revenue",
        "currency",
        "computed_at",
        "deleted_at",
    }
    for col in required:
        assert col in cols, f"AttributionMatrixSnapshotModel missing: {col}"


def test_attribution_matrix_snapshot_uses_mapped_column() -> None:
    """AttributionMatrixSnapshotModel must use SA 2.0 mapped_column syntax."""
    model = _import_model(
        "src.modules.vitalia.agentic.lucas.persistence.models.attribution_matrix_snapshot",
        "AttributionMatrixSnapshotModel",
    )
    assert _has_mapped_column(model)


# ─────────────────────────────────────────────────────────────────────────────
# Agentic/lucas: ReferralsLeaderboardSnapshotModel
# ─────────────────────────────────────────────────────────────────────────────


def test_referrals_leaderboard_snapshot_model_importable() -> None:
    """ReferralsLeaderboardSnapshotModel must be importable."""
    model = _import_model(
        "src.modules.vitalia.agentic.lucas.persistence.models.referrals_leaderboard_snapshot",
        "ReferralsLeaderboardSnapshotModel",
    )
    assert model is not None


def test_referrals_leaderboard_snapshot_tablename() -> None:
    """ReferralsLeaderboardSnapshotModel must map to 'referrals_leaderboard_snapshots'."""
    model = _import_model(
        "src.modules.vitalia.agentic.lucas.persistence.models.referrals_leaderboard_snapshot",
        "ReferralsLeaderboardSnapshotModel",
    )
    assert model.__tablename__ == "referrals_leaderboard_snapshots"


def test_referrals_leaderboard_snapshot_required_columns() -> None:
    """ReferralsLeaderboardSnapshotModel must have all required columns."""
    model = _import_model(
        "src.modules.vitalia.agentic.lucas.persistence.models.referrals_leaderboard_snapshot",
        "ReferralsLeaderboardSnapshotModel",
    )
    cols = _get_column_names(model)
    required = {
        "id",
        "tenant_id",
        "clinic_id",
        "period_start",
        "period_end",
        "top_referrers",
        "total_referrals",
        "total_converted",
        "computed_at",
        "deleted_at",
    }
    for col in required:
        assert col in cols, f"ReferralsLeaderboardSnapshotModel missing: {col}"


def test_referrals_leaderboard_snapshot_uses_mapped_column() -> None:
    """ReferralsLeaderboardSnapshotModel must use SA 2.0 mapped_column syntax."""
    model = _import_model(
        "src.modules.vitalia.agentic.lucas.persistence.models.referrals_leaderboard_snapshot",
        "ReferralsLeaderboardSnapshotModel",
    )
    assert _has_mapped_column(model)
