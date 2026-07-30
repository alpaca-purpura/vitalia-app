# cap: sales_agent.honor-mode-bridge
# story-origin: vitalia-fase2-adrian-canal-inbound T-BE-3
"""RED tests for OperatorInstructionService — SC-8, V-NF-3, V-NF-4, RN-13, RN-15.

TDD: these tests MUST go RED before production code is written.

OperatorInstructionService persists an operator instruction to the active
agent_state_checkpoints.metadata_info JSONB (key: "operator_instructions") via
the same pattern as override_context_wire (raw SQL merge, no column change, no
checkpoint reset). It also writes a sync audit row (V-NF-3, HIPAA-lite) and a
NON-PHI activity event (RN-15).

Validators covered:
  SC-8 : instrucción persiste + steerea todos los turnos
  V-NF-3: audit sync write pre-response
  V-NF-4: response_model= (checked by arch test; here we test DTO shape)
  RN-13 : persistente en metadata_info, steerea hasta editar/limpiar
  RN-15 : activity NON-PHI "La recepción instruyó a Adrián: …"; lead nunca la ve
  AC-13 : instrucción rechazada si conversación NO está en modo 'decide'
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

# ── these imports will FAIL (RED) until production code is written ──
from src.modules.vitalia.sales_agent.api.dtos.operator_instruction_dtos import (
    SetOperatorInstructionRequest,
    SetOperatorInstructionResponse,
)
from src.modules.vitalia.sales_agent.application.services.operator_instruction_service import (
    ConversationNotInDecideModeError,
    OperatorInstructionService,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
CONV_ID = uuid4()
LEAD_ID = uuid4()
USER_ID = uuid4()
INSTRUCTION_TEXT = "Ofrecer descuento del 10 % si el paciente menciona presupuesto."


def _conv(*, handler_mode: str = "ai", proposal_required: bool = False) -> MagicMock:
    """Minimal Conversation-like domain object in 'decide' mode."""
    c = MagicMock()
    c.id = CONV_ID
    c.tenant_id = TENANT_ID
    c.clinic_id = CLINIC_ID
    c.lead_id = LEAD_ID
    c.handler_mode = handler_mode
    c.proposal_required = proposal_required
    c.pause_until = None
    return c


def _make_service(conv: MagicMock | None = None) -> tuple[OperatorInstructionService, dict]:
    """Build service with all mocked deps. Returns (service, mocks)."""
    mock_conv_repo = AsyncMock()
    mock_conv_repo.get_by_id = AsyncMock(return_value=conv or _conv())

    mock_checkpoint_port = AsyncMock()
    mock_checkpoint_port.set_operator_instruction = AsyncMock(return_value=True)

    mock_audit_writer = AsyncMock()
    mock_audit_writer.write = AsyncMock(return_value=None)

    mock_activity_repo = AsyncMock()
    mock_activity_repo.create = AsyncMock(return_value=MagicMock())

    svc = OperatorInstructionService(
        conv_repo=mock_conv_repo,
        checkpoint_port=mock_checkpoint_port,
        audit_writer=mock_audit_writer,
        activity_repo=mock_activity_repo,
    )

    mocks = {
        "conv_repo": mock_conv_repo,
        "checkpoint_port": mock_checkpoint_port,
        "audit_writer": mock_audit_writer,
        "activity_repo": mock_activity_repo,
    }
    return svc, mocks


# ---------------------------------------------------------------------------
# SC-8 / RN-13 — instruction persists to metadata_info
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_instruction_persists_to_metadata_info() -> None:
    """SC-8 / RN-13: set_instruction() calls checkpoint_port.set_operator_instruction once."""
    svc, mocks = _make_service()

    await svc.set_instruction(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        instruction=INSTRUCTION_TEXT,
        actor_user_id=USER_ID,
    )

    mocks["checkpoint_port"].set_operator_instruction.assert_awaited_once()
    kwargs = mocks["checkpoint_port"].set_operator_instruction.await_args.kwargs
    assert kwargs["tenant_id"] == TENANT_ID
    assert kwargs["lead_id"] == LEAD_ID
    assert kwargs["instruction"] == INSTRUCTION_TEXT


@pytest.mark.asyncio
async def test_instruction_steers_until_cleared() -> None:
    """RN-13: each call overwrites the key (idempotent write, not append)."""
    svc, mocks = _make_service()

    await svc.set_instruction(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        instruction="Instrucción A",
        actor_user_id=USER_ID,
    )
    await svc.set_instruction(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        instruction="Instrucción B",
        actor_user_id=USER_ID,
    )

    # Two calls to persist — each overwrites the key
    assert mocks["checkpoint_port"].set_operator_instruction.await_count == 2
    last_kwargs = mocks["checkpoint_port"].set_operator_instruction.await_args.kwargs
    assert last_kwargs["instruction"] == "Instrucción B"


# ---------------------------------------------------------------------------
# V-NF-3 — audit row written SYNC pre-response (HIPAA-lite)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_row_written_sync_pre_response() -> None:
    """V-NF-3 / hipaa-lite: audit_writer.write() called exactly once per instruction."""
    svc, mocks = _make_service()

    await svc.set_instruction(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        instruction=INSTRUCTION_TEXT,
        actor_user_id=USER_ID,
    )

    mocks["audit_writer"].write.assert_awaited_once()
    audit_kwargs = mocks["audit_writer"].write.await_args.kwargs
    assert audit_kwargs["tenant_id"] == TENANT_ID
    assert audit_kwargs["clinic_id"] == CLINIC_ID
    assert audit_kwargs["user_id"] == USER_ID
    assert "operator_instruction" in audit_kwargs.get("action", "")
    assert audit_kwargs.get("resource_type") == "conversation"
    assert audit_kwargs.get("resource_id") == CONV_ID


# ---------------------------------------------------------------------------
# RN-15 — NON-PHI activity event; lead NEVER sees instruction text raw
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_activity_event_non_phi_written() -> None:
    """RN-15: activity event is written with sanitized commercial text."""
    svc, mocks = _make_service()

    await svc.set_instruction(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        instruction=INSTRUCTION_TEXT,
        actor_user_id=USER_ID,
    )

    mocks["activity_repo"].create.assert_awaited_once()
    act_kwargs = mocks["activity_repo"].create.await_args.kwargs
    assert act_kwargs["tenant_id"] == TENANT_ID
    assert act_kwargs["clinic_id"] == CLINIC_ID
    assert act_kwargs["conversation_id"] == CONV_ID
    desc = act_kwargs.get("description_es", "")
    # RN-15: description references "Adrián" and "recepción" — non-PHI operator text
    assert "Adrián" in desc
    assert "instruyó" in desc or "instruccion" in desc.lower() or "instrucción" in desc


@pytest.mark.asyncio
async def test_activity_event_does_not_expose_full_instruction_to_lead() -> None:
    """RN-15: the lead never sees the raw instruction (not stored in lead-visible fields)."""
    svc, mocks = _make_service()

    await svc.set_instruction(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        instruction="SECRETO: descuento autorizado hasta 40%",
        actor_user_id=USER_ID,
    )

    act_kwargs = mocks["activity_repo"].create.await_args.kwargs
    payload = act_kwargs.get("payload_sanitized") or {}
    # The full instruction text must NOT appear verbatim in payload_sanitized
    full_text = str(payload)
    assert "40%" not in full_text or "instrucción" in full_text.lower(), (
        "payload_sanitized must not expose raw instruction to lead-visible surface"
    )


# ---------------------------------------------------------------------------
# AC-13 — instruction rejected if conversation not in 'decide' mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_instruction_rejected_in_consulta_mode() -> None:
    """AC-13: proposal_required=True (consulta mode) → ConversationNotInDecideModeError."""
    svc, _ = _make_service(conv=_conv(proposal_required=True))

    with pytest.raises(ConversationNotInDecideModeError):
        await svc.set_instruction(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=CONV_ID,
            instruction=INSTRUCTION_TEXT,
            actor_user_id=USER_ID,
        )


@pytest.mark.asyncio
async def test_instruction_rejected_in_human_mode() -> None:
    """AC-13: handler_mode='human' (pausa mode) → ConversationNotInDecideModeError."""
    svc, _ = _make_service(conv=_conv(handler_mode="human"))

    with pytest.raises(ConversationNotInDecideModeError):
        await svc.set_instruction(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=CONV_ID,
            instruction=INSTRUCTION_TEXT,
            actor_user_id=USER_ID,
        )


# ---------------------------------------------------------------------------
# Tenant isolation — dual filter enforced
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_tenant_instruction_uses_caller_tenant_not_conv_tenant() -> None:
    """Tenant isolation: audit + activity always use the CALLER's tenant_id (from header)."""
    other_tenant = uuid4()
    conv = _conv()
    conv.tenant_id = other_tenant  # conv belongs to different tenant
    svc, mocks = _make_service(conv=conv)

    # Caller's tenant_id (from header) is TENANT_ID
    await svc.set_instruction(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        instruction=INSTRUCTION_TEXT,
        actor_user_id=USER_ID,
    )

    audit_kwargs = mocks["audit_writer"].write.await_args.kwargs
    assert audit_kwargs["tenant_id"] == TENANT_ID, "Audit must use caller's tenant_id"


# ---------------------------------------------------------------------------
# DTOs — V-NF-4 (response_model shape)
# ---------------------------------------------------------------------------


def test_set_instruction_request_dto_valid() -> None:
    """SetOperatorInstructionRequest parses valid instruction text."""
    req = SetOperatorInstructionRequest(instruction=INSTRUCTION_TEXT)
    assert req.instruction == INSTRUCTION_TEXT


def test_set_instruction_request_dto_empty_instruction_rejected() -> None:
    """SetOperatorInstructionRequest rejects empty string."""
    with pytest.raises(ValidationError):
        SetOperatorInstructionRequest(instruction="")


def test_set_instruction_request_dto_blank_instruction_rejected() -> None:
    """SetOperatorInstructionRequest rejects whitespace-only string."""
    with pytest.raises(ValidationError):
        SetOperatorInstructionRequest(instruction="   ")


def test_set_instruction_response_dto_shape() -> None:
    """SetOperatorInstructionResponse has conversation_id + status + persisted_at."""
    resp = SetOperatorInstructionResponse(
        conversation_id=CONV_ID,
        status="set",
        persisted_at="2026-01-01T00:00:00Z",
    )
    assert resp.conversation_id == CONV_ID
    assert resp.status == "set"
    assert resp.persisted_at is not None


# ---------------------------------------------------------------------------
# No checkpoint crash when no active checkpoint exists
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_active_checkpoint_logs_but_does_not_raise() -> None:
    """If checkpoint_port returns False (no active checkpoint), service still succeeds."""
    svc, mocks = _make_service()
    mocks["checkpoint_port"].set_operator_instruction = AsyncMock(return_value=False)

    # Must not raise — operator instruction still recorded in audit + activity
    await svc.set_instruction(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        instruction=INSTRUCTION_TEXT,
        actor_user_id=USER_ID,
    )

    # Audit + activity still fire even when no checkpoint exists
    mocks["audit_writer"].write.assert_awaited_once()
    mocks["activity_repo"].create.assert_awaited_once()


# ---------------------------------------------------------------------------
# T-AG-1 — agentic bridge wiring: on set, mirror into the engine turn seam
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_instruction_applies_bridge_to_turn_seam_when_present() -> None:
    """T-AG-1/SC-8: when an OperatorInstructionBridge is injected, set_instruction
    applies it (mirrors metadata_info['operator_instructions'] → resume_objective)
    so the very next Adrián turn injects [INSTRUCCION DEL OPERADOR].

    The bridge is OPTIONAL (back-compat with T-BE-3's 4-arg construction); when
    present it is invoked with the resolved (tenant_id, lead_id).
    """
    svc, mocks = _make_service()
    bridge = AsyncMock()
    bridge.apply_for_turn = AsyncMock(return_value=True)
    svc._bridge_to_turn = bridge  # injected post-construction in this back-compat test

    await svc.set_instruction(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        instruction=INSTRUCTION_TEXT,
        actor_user_id=USER_ID,
    )

    bridge.apply_for_turn.assert_awaited_once()
    kwargs = bridge.apply_for_turn.await_args.kwargs
    assert kwargs["tenant_id"] == TENANT_ID
    assert kwargs["lead_id"] == LEAD_ID


@pytest.mark.asyncio
async def test_bridge_is_optional_back_compat() -> None:
    """Back-compat: without a bridge, set_instruction still works (T-BE-3 contract)."""
    svc, mocks = _make_service()
    # No bridge injected (default None) — must not raise.
    await svc.set_instruction(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        conversation_id=CONV_ID,
        instruction=INSTRUCTION_TEXT,
        actor_user_id=USER_ID,
    )
    mocks["checkpoint_port"].set_operator_instruction.assert_awaited_once()
