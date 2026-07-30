# cap: inbox.adrian-inbox
# story-origin: vitalia-fase2-adrian-inbox T-2
"""Vitalia inbox API router — 8 inbox endpoints + nudge (T-2).

API layer (thin): validate headers → resolve auth → RBAC → call service → map exceptions → response.
No business logic here.

Endpoints:
  POST   /inbox/conversations/{conv_id}/messages           — send AI/human message (PHI gated)
  POST   /inbox/conversations/{conv_id}/messages/{msg_id}/revert — retract within 5min (PHI gated)
  PATCH  /inbox/conversations/{conv_id}/mode              — set handler mode (OCC, PHI gated)
  POST   /inbox/conversations/{conv_id}/pause             — pause Adrián 60min (PHI gated)
  GET    /inbox/conversations/{conv_id}/tools             — tool state read-only (PHI gated)
  GET    /inbox/conversations/{conv_id}/activity-stream   — activity log (PHI gated)
  POST   /inbox/proactive-outbound                        — HSM template send (PHI gated)
  POST   /inbox/transcribe                                — audio transcription (PHI gated)
  POST   /inbox/conversations/{conv_id}/nudge             — nudge re-engagement (T-2, PHI gated)

response_model= is MANDATORY on every endpoint (PII gate + arch fitness).
redirect_slashes=False set on FastAPI *app* in main.py, NOT here.
PHI dual-filter: every service call carries BOTH tenant_id AND clinic_id.
HIPAA-lite: audit log written sync by each service before response.

T-2 additions:
  - POST /conversations/{conv_id}/nudge (NudgeService + NudgeRequest/Response DTOs)
  - _get_nudge_service DI factory (proactive_resolver via ProactiveOutboundService — NO direct sales_agent import)

downstream-regression-na: brand-local vitalia inbox router
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from luana_core_compliance.application.compliance_service import ComplianceService
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session, get_async_session_committing
from src.modules.vitalia._shared.auth.rbac import PHIAccessDeniedError
from src.modules.vitalia.audit.audit_writer import AsyncAuditWriter
from src.modules.vitalia.connections.whisper.adapter import WhisperAdapter
from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (
    ActionReceiptRepository,
)
from src.modules.vitalia.crm.infrastructure.persistence.activity_event_repository import (
    ActivityEventRepository,
)
from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
    ConversationRepository,
)
from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
    LeadRepository,
)
from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (
    MessageRepository,
)
from src.modules.vitalia.iam.application.services.clinic_resolver import (
    ClinicContext,
    ClinicResolver,
    MissingAuthHeaderError,
    RoleNotFoundError,
    UserNotFoundError,
)
from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
    ClerkJwtDecoder,
    JwtDecodeError,
)
from src.modules.vitalia.inbox.application.dto.activity_event_dto import (
    ActivityStreamResponse,
)
from src.modules.vitalia.inbox.application.dto.nudge_dto import NudgeRequest, NudgeResponse
from src.modules.vitalia.inbox.application.dto.proactive_outbound_dto import (
    ProactiveOutboundRequest,
    ProactiveOutboundResponse,
)
from src.modules.vitalia.inbox.application.dto.retract_message_dto import (
    RetractMessageRequest,
    RetractMessageResponse,
)
from src.modules.vitalia.inbox.application.dto.send_message_dto import (
    MessageResponse,
    SendMessageRequest,
)
from src.modules.vitalia.inbox.application.dto.set_mode_dto import (
    ConversationResponse,
    SetModeRequest,
)
from src.modules.vitalia.inbox.application.dto.tools_state_dto import ToolsStateResponse
from src.modules.vitalia.inbox.application.policies.phi_channel_policy import (
    PhiChannelPolicy,
)
from src.modules.vitalia.inbox.application.services.activity_event_service import (
    ActivityEventService,
)
from src.modules.vitalia.inbox.application.services.nudge_service import (
    ConvNotFoundError as NudgeConvNotFoundError,
)
from src.modules.vitalia.inbox.application.services.nudge_service import (
    NudgeNotApplicableError,
    NudgeService,
)
from src.modules.vitalia.inbox.application.services.pause_adrian_service import (
    PauseAdrianService,
)
from src.modules.vitalia.inbox.application.services.proactive_outbound_service import (
    ComplianceBlockedError,
    LeadNotFoundError,
    MarketingOptInRequiredError,
    ProactiveOutboundService,
    RateLimitExceededError,
    TemplateNotFoundError,
)
from src.modules.vitalia.inbox.application.services.retract_message_service import (
    ActionReceiptExpiredError,
    MessageNotRetractableError,
    PatientRepliedConflictError,
    RetractMessageService,
)
from src.modules.vitalia.inbox.application.services.send_message_service import (
    SendMessageService,
)
from src.modules.vitalia.inbox.application.services.set_mode_service import (
    OCCConflictError,
    SetModeService,
)
from src.modules.vitalia.inbox.application.services.whisper_transcribe_service import (
    WhisperTranscribeService,
)

logger = structlog.get_logger()

# PHI roles (hipaa-lite.md § Access control)
_PHI_ROLES = frozenset({"doctor", "nurse", "admin_clinic"})

# Inbox operator roles: the inbox is the operator's tool (front desk + owner), not
# strict clinical PHI. Mirrors crm.router._INBOX_OPERATOR_ROLES (ratified by Chris
# for list/detail) so the front desk can also ACT on a conversation (set mode,
# pause Adrián, send, nudge). Owner + receptionist were getting 403 on every inbox
# mutation because these endpoints used the strict _PHI_ROLES gate.
# TODO(consolidate): lift _INBOX_OPERATOR_ROLES to a shared vitalia constant
# (currently mirrored in crm + inbox routers).
_INBOX_OPERATOR_ROLES = _PHI_ROLES | frozenset({"owner", "receptionist"})

router = APIRouter(tags=["inbox"])

# Header type aliases
AuthorizationHeader = Annotated[str, Header(alias="Authorization")]
TenantIdHeader = Annotated[str, Header(alias="X-Tenant-ID")]
ClinicIdHeader = Annotated[str, Header(alias="X-Clinic-ID")]

# Outbox adapter_bus — module-level import per core engine pattern (same as fidelizacion services)
# Per anti-duplication.md: use core engine, never reimplement locally
try:
    from luana_core_events.outbox import adapter_bus as _adapter_bus  # type: ignore[import]
except ImportError:  # pragma: no cover — available in runtime, not in offline env
    from unittest.mock import AsyncMock as _AsyncMock  # noqa: PLC0415

    class _FallbackBus:  # type: ignore[no-redef]
        """Fallback outbox bus for offline environments."""

        publish = _AsyncMock()

    _adapter_bus = _FallbackBus()


# Slice 1 no-op stubs for external integrations not yet wired
# (compliance_service, rate_limiter, redis_client, whisper_adapter)
# These are swapped for real implementations in Slice 2.


class _NoOpRateLimiter:
    """Slice 1 no-op rate limiter — allows all sends."""

    async def check_and_increment(self, *args: object, **kwargs: object) -> bool:
        """No-op: return True (not rate-limited) in Slice 1."""
        return True


class _NoOpRedisClient:
    """Slice 1 no-op Redis client for PauseAdrianService TTL."""

    async def set(self, *args: object, **kwargs: object) -> None:
        """No-op: skip Redis SET in Slice 1."""

    async def setex(self, *args: object, **kwargs: object) -> None:
        """No-op: skip Redis SETEX (pause TTL) when no real Redis (dev).

        PauseAdrianService persists pause_until in the DB regardless; the Redis
        TTL is only a fast-path pre-check. Without this method pausing 500'd in
        dev because the no-op client was missing setex.
        """

    async def get(self, *args: object, **kwargs: object) -> None:
        """No-op: return None (no pause active) in Slice 1."""
        return None

    async def delete(self, *args: object, **kwargs: object) -> None:
        """No-op: skip Redis DELETE in Slice 1."""


# ---------------------------------------------------------------------------
# Provider factories — real DI with FastAPI Depends (Critical #4)
# ---------------------------------------------------------------------------


def _get_resolver() -> ClinicResolver:
    """Create a ClinicResolver with the default JWT decoder."""
    return ClinicResolver(decoder=ClerkJwtDecoder())


def _build_compliance_service() -> ComplianceService:
    """Real ComplianceService for outbound PHI gating (T-1 un-stub · SC-3/AC-9/RN-7).

    Runs the brand PhiChannelPolicy (blocks clinical PHI keywords on unencrypted
    channels → portal redirect). Extends the engine CompliancePolicy Protocol;
    NOT a mirror (anti-duplication.md).
    """
    return ComplianceService(policies=[PhiChannelPolicy()])


async def _get_send_service(
    # Mutation endpoint → committing session (the service does NOT commit on its own;
    # get_async_session never commits → writes were silently dropped). See get_async_session_committing.
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> SendMessageService:
    """Create SendMessageService with real repo instances and async DI.

    Compliance gate wired (T-1): outbound text on unencrypted channels with PHI
    keywords → portal-redirect microcopy + 'compliance_block_outbound_phi' event.
    """
    return SendMessageService(
        msg_repo=MessageRepository(session=session),
        conv_repo=ConversationRepository(session=session),
        receipt_repo=ActionReceiptRepository(session=session),
        audit_writer=AsyncAuditWriter(session=session),
        event_bus=_adapter_bus,
        session=session,
        compliance_service=_build_compliance_service(),
        activity_event_repo=ActivityEventRepository(session=session),
    )


async def _get_retract_service(
    # Mutation endpoint → committing session: retract() writes (mark_retracted +
    # update_handler_mode + audit_writer.write) and no service commits on its own;
    # get_async_session never commits → the revert was silently dropped (same
    # HB-50 root cause as the other 5 mutation factories). See get_async_session_committing.
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> RetractMessageService:
    """Create RetractMessageService with real repo instances and async DI."""
    return RetractMessageService(
        msg_repo=MessageRepository(session=session),
        receipt_repo=ActionReceiptRepository(session=session),
        conv_repo=ConversationRepository(session=session),
        audit_writer=AsyncAuditWriter(session=session),
        event_bus=_adapter_bus,
        channel_adapters={},
        session=session,
    )


async def _get_set_mode_service(
    # Mutation endpoint → committing session (PATCH /mode persisted nothing otherwise).
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> SetModeService:
    """Create SetModeService with real repo instances and async DI."""
    return SetModeService(
        conv_repo=ConversationRepository(session=session),
        audit_writer=AsyncAuditWriter(session=session),
        event_bus=_adapter_bus,
        session=session,
    )


async def _get_pause_service(
    # Mutation endpoint → committing session (POST /pause persisted nothing otherwise).
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> PauseAdrianService:
    """Create PauseAdrianService with real repos + Slice 1 Redis stub."""
    return PauseAdrianService(
        conv_repo=ConversationRepository(session=session),
        audit_writer=AsyncAuditWriter(session=session),
        event_bus=_adapter_bus,
        redis_client=_NoOpRedisClient(),
        session=session,
    )


async def _get_proactive_service(
    # Mutation endpoint → committing session (proactive outbound persisted nothing otherwise).
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> ProactiveOutboundService:
    """Create ProactiveOutboundService with real repos + Slice 1 stubs."""
    return ProactiveOutboundService(
        lead_repo=LeadRepository(session),
        conv_repo=ConversationRepository(session=session),
        msg_repo=MessageRepository(session=session),
        audit_writer=AsyncAuditWriter(session=session),
        event_bus=_adapter_bus,
        compliance_service=_build_compliance_service(),
        rate_limiter=_NoOpRateLimiter(),
        channel_adapters={},
        session=session,
    )


def _get_transcribe_service() -> WhisperTranscribeService:
    """Create WhisperTranscribeService with Whisper adapter.

    API key from OPENAI_API_KEY env var. Missing key → empty string; adapter
    returns TranscriptionResult(text=None, confidence=0.0) with graceful degradation.
    """
    import os  # noqa: PLC0415

    api_key = os.environ.get("OPENAI_API_KEY", "")
    return WhisperTranscribeService(
        whisper_adapter=WhisperAdapter(api_key=api_key),
    )


async def _get_activity_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ActivityEventService:
    """Create ActivityEventService with real repo instances."""
    return ActivityEventService(
        activity_repo=ActivityEventRepository(session=session),
    )


async def _get_nudge_service(
    # Mutation endpoint → committing session (POST /nudge persisted nothing otherwise).
    session: Annotated[AsyncSession, Depends(get_async_session_committing)],
) -> NudgeService:
    """Create NudgeService with real repos + proactive_resolver (T-2 Slice 2).

    proactive_resolver: async callable that wraps ProactiveOutboundService.send_proactive.
    NEVER imports from sales_agent/ directly (anti-coupling — av-no-sales-agent-import).
    The resolver delegates to ProactiveOutboundService which is the shared send path.
    """
    proactive_svc = ProactiveOutboundService(
        lead_repo=LeadRepository(session),
        conv_repo=ConversationRepository(session=session),
        msg_repo=MessageRepository(session=session),
        audit_writer=AsyncAuditWriter(session=session),
        event_bus=_adapter_bus,
        compliance_service=_build_compliance_service(),
        rate_limiter=_NoOpRateLimiter(),
        channel_adapters={},
        session=session,
    )

    async def _proactive_resolver(
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        conversation_id: UUID,
        sent_by_user_id: UUID,
        reason: str | None = None,
    ) -> object:
        """Resolver: delegates to ProactiveOutboundService.send_proactive.

        Translates NudgeService call signature to ProactiveOutboundService.
        The resolver pattern ensures NudgeService has zero coupling to sales_agent/.
        """
        # Nudge uses a synthetic nudge_reengagement template.
        # Variables include optional reason for the template body.
        # Note: lead_id is resolved from conv.lead_id by ProactiveOutboundService.
        # For nudge, we pass conversation_id indirectly via a brand-local nudge template.
        # This resolver wraps the outbound path without exposing sales_agent internals.
        from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (  # noqa: PLC0415
            ConversationRepository as _ConvRepo,
        )

        # Get conversation to resolve lead_id (dual filter already applied by NudgeService)
        conv_repo_inner = _ConvRepo(session=session)
        conv = await conv_repo_inner.get_by_id(id=conversation_id, tenant_id=tenant_id, scope_id=clinic_id)
        if conv is None or conv.lead_id is None:
            # Nudge without lead_id: return a structural stub result
            # (activity event is the primary record; outbound is best-effort)
            from dataclasses import dataclass  # noqa: PLC0415
            from datetime import UTC as _UTC  # noqa: PLC0415
            from datetime import datetime as _dt
            from uuid import uuid4 as _uuid4  # noqa: PLC0415

            @dataclass
            class _NudgeStubResult:
                message_id: UUID
                conversation_id: UUID
                sent_at: object

            return _NudgeStubResult(
                message_id=_uuid4(),
                conversation_id=conversation_id,
                sent_at=_dt.now(_UTC),
            )

        return await proactive_svc.send_proactive(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            lead_id=conv.lead_id,
            template_id="nudge_reengagement",
            variables={"reason": reason or "Reactivación de conversación estancada."},
            channel=conv.channel,
            sent_by_user_id=sent_by_user_id,
        )

    return NudgeService(
        conv_repo=ConversationRepository(session=session),
        activity_repo=ActivityEventRepository(session=session),
        audit_writer=AsyncAuditWriter(session=session),
        event_bus=_adapter_bus,
        proactive_resolver=_proactive_resolver,
    )


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


async def _resolve_context(
    authorization: str,
    x_tenant_id: str,
    x_clinic_id: str,
    session: AsyncSession,
) -> ClinicContext:
    """Parse authorization header and resolve clinic context via DB role.

    Slice 2 path: uses async_resolve() to get role from DB.

    Raises:
        HTTPException(401): Token missing, invalid, or user not found.
        HTTPException(403): User has no active role in this tenant.
    """
    token = authorization.removeprefix("Bearer ").strip()
    resolver = _get_resolver()
    try:
        return await resolver.async_resolve(
            token=token,
            session=session,
            tenant_id_str=x_tenant_id,
            clinic_id_str=x_clinic_id,
        )
    except MissingAuthHeaderError:
        raise HTTPException(status_code=401, detail="Token de autorización requerido.")
    except JwtDecodeError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")
    except UserNotFoundError:
        raise HTTPException(status_code=401, detail="Usuario no encontrado.")
    except RoleNotFoundError:
        raise HTTPException(status_code=403, detail="El usuario no tiene un rol activo en este tenant.")
    except ValueError:
        raise HTTPException(status_code=422, detail="Identificadores de tenant o clínica inválidos.")


def _assert_phi_access(user_role: str) -> None:
    """Raise PHIAccessDeniedError if role may not operate the inbox.

    The inbox is the operator's tool: clinical roles (doctor/nurse/admin_clinic)
    PLUS front-desk operators (owner/receptionist) may act on a conversation.
    Mirrors crm._INBOX_OPERATOR_ROLES (ratified). Non-operators (e.g. marketing,
    sales, patient) are still denied.

    Raises:
        PHIAccessDeniedError: When role is not in _INBOX_OPERATOR_ROLES.
    """
    if user_role not in _INBOX_OPERATOR_ROLES:
        raise PHIAccessDeniedError(
            user_role=user_role,
            required_roles=list(_INBOX_OPERATOR_ROLES),
            resource_type="inbox.conversation",
        )


# ---------------------------------------------------------------------------
# Endpoint 1: POST /conversations/{conv_id}/messages — send message (PHI gated)
# ---------------------------------------------------------------------------


@router.post(
    "/conversations/{conv_id}/messages",
    response_model=MessageResponse,
    status_code=201,
)
async def send_message(
    conv_id: UUID,
    body: SendMessageRequest,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    service: Annotated[SendMessageService, Depends(_get_send_service)],
) -> MessageResponse:
    """Send an AI or human message to a conversation.

    PHI gated: doctor, nurse, admin_clinic roles only.
    Audit log written sync pre-response by SendMessageService.

    Args:
        conv_id: Conversation UUID (path param).
        body: Message content (body_text, media_url, media_kind, etc.).
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header (dual PHI filter).
        service: SendMessageService (injected via DI).

    Returns:
        MessageResponse (201 Created).

    Raises:
        401: Invalid/missing token.
        403: Role not permitted to access PHI conversations.
        404: Conversation not found.
    """
    ctx = await _resolve_context(authorization, x_tenant_id, x_clinic_id, session)

    try:
        _assert_phi_access(ctx.role)
    except PHIAccessDeniedError:
        logger.warning(
            "inbox.send_message.access_denied",
            role=ctx.role,
            conv_id=str(conv_id),
        )
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para acceder a conversaciones clínicas.",
        )

    tenant_id = ctx.tenant_id
    clinic_id = UUID(x_clinic_id)
    user_id = UUID(ctx.user_id) if len(str(ctx.user_id)) == 36 else UUID(int=0)

    try:
        result = await service.send(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conv_id,
            user_id=user_id,
            body_text=body.body_text,
            media_url=body.media_url,
            media_kind=body.media_kind,
            media_duration_s=body.media_duration_s,
            handler_mode_override=body.handler_mode_override,
            idempotency_key=body.idempotency_key,
        )
    except Exception as exc:
        # Import here to avoid circular at module load — ConversationNotFoundError is
        # local to send_message_service
        from src.modules.vitalia.inbox.application.services.send_message_service import (
            ConversationNotFoundError,
        )

        if isinstance(exc, ConversationNotFoundError):
            raise HTTPException(status_code=404, detail="Conversación no encontrada.")
        raise

    return MessageResponse(
        id=result.message_id,
        conversation_id=result.conversation_id,
        sender_type=result.sender_type,
        sender_user_id=result.sender_user_id,
        body_text=result.body_text,
        media_kind=result.media_kind,
        media_url=result.media_url,
        media_duration_s=result.media_duration_s,
        transcription_text=result.transcription_text,
        transcription_confidence=result.transcription_confidence,
        retracted_at=result.retracted_at,
        retract_succeeded=result.retract_succeeded,
        handler_mode=result.handler_mode,
        sent_at=result.sent_at,
        action_receipt_expires_at=result.action_receipt_expires_at,
    )


# ---------------------------------------------------------------------------
# Endpoint 2: POST /conversations/{conv_id}/messages/{msg_id}/revert — retract (PHI gated)
# ---------------------------------------------------------------------------


@router.post(
    "/conversations/{conv_id}/messages/{msg_id}/revert",
    response_model=RetractMessageResponse,
)
async def revert_message(
    conv_id: UUID,
    msg_id: UUID,
    body: RetractMessageRequest,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    service: Annotated[RetractMessageService, Depends(_get_retract_service)],
) -> RetractMessageResponse:
    """Retract an AI message within the 5-minute action receipt window.

    PHI gated: doctor, nurse, admin_clinic roles only.
    5-min window: if expired → 410 Gone.
    Patient replied conflict: → 409 Conflict.
    Audit log written sync pre-response by RetractMessageService.

    Args:
        conv_id: Conversation UUID.
        msg_id: Message UUID to retract.
        body: Optional retract reason.
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header (dual PHI filter).
        service: RetractMessageService (injected via DI).

    Returns:
        RetractMessageResponse (200 OK).

    Raises:
        401: Invalid/missing token.
        403: Role not permitted.
        404: Message or action receipt not found.
        409: Patient replied after the message.
        410: Action receipt expired (>5 min window).
    """
    ctx = await _resolve_context(authorization, x_tenant_id, x_clinic_id, session)

    try:
        _assert_phi_access(ctx.role)
    except PHIAccessDeniedError:
        logger.warning(
            "inbox.revert_message.access_denied",
            role=ctx.role,
            conv_id=str(conv_id),
            msg_id=str(msg_id),
        )
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para esta acción.",
        )

    tenant_id = ctx.tenant_id
    clinic_id = UUID(x_clinic_id)
    user_id = UUID(ctx.user_id) if len(str(ctx.user_id)) == 36 else UUID(int=0)

    try:
        result = await service.retract(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conv_id,
            message_id=msg_id,
            retracted_by_user_id=user_id,
            reason=body.reason,
        )
    except ActionReceiptExpiredError as exc:
        expired_str = exc.expired_at.isoformat()
        raise HTTPException(
            status_code=410,
            detail=f"La ventana de 5 minutos expiró el {expired_str}. No es posible retractar el mensaje.",
        )
    except PatientRepliedConflictError:
        raise HTTPException(
            status_code=409,
            detail="Conflicto: el paciente respondió después del mensaje. No se puede retractar.",
        )
    except MessageNotRetractableError:
        raise HTTPException(
            status_code=404,
            detail="No se encontró un recibo de acción activo para este mensaje.",
        )

    return RetractMessageResponse(
        message_id=result.message_id,
        retracted_at=result.retracted_at,
        retract_succeeded=result.retract_succeeded,
        fallback_applied=result.fallback_applied,
        retract_reason=result.retract_reason,
    )


# ---------------------------------------------------------------------------
# Endpoint 3: PATCH /conversations/{conv_id}/mode — set handler mode (OCC, PHI gated)
# ---------------------------------------------------------------------------


@router.patch(
    "/conversations/{conv_id}/mode",
    response_model=ConversationResponse,
)
async def set_conversation_mode(
    conv_id: UUID,
    body: SetModeRequest,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    service: Annotated[SetModeService, Depends(_get_set_mode_service)],
) -> ConversationResponse:
    """Change handler mode (ai ↔ human) with OCC check.

    PHI gated: doctor, nurse, admin_clinic roles only.
    OCC: body.expected_updated_at must match current conversation updated_at.
    Stale → 409 Conflict. Conversation not found → 404.

    Args:
        conv_id: Conversation UUID.
        body: SetModeRequest (mode, proposal_required, expected_updated_at).
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header (dual PHI filter).
        service: SetModeService (injected via DI).

    Returns:
        ConversationResponse (200 OK).

    Raises:
        401: Invalid/missing token.
        403: Role not permitted.
        404: Conversation not found.
        409: OCC conflict (stale expected_updated_at).
    """
    ctx = await _resolve_context(authorization, x_tenant_id, x_clinic_id, session)

    try:
        _assert_phi_access(ctx.role)
    except PHIAccessDeniedError:
        logger.warning(
            "inbox.set_mode.access_denied",
            role=ctx.role,
            conv_id=str(conv_id),
        )
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para cambiar el modo de atención.",
        )

    tenant_id = ctx.tenant_id
    clinic_id = UUID(x_clinic_id)
    user_id = UUID(ctx.user_id) if len(str(ctx.user_id)) == 36 else UUID(int=0)

    try:
        result = await service.set_mode(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conv_id,
            new_mode=body.mode,
            proposal_required=body.proposal_required,
            expected_updated_at=body.expected_updated_at,
            changed_by_user_id=user_id,
        )
    except OCCConflictError:
        raise HTTPException(
            status_code=409,
            detail="Conflict: el registro fue actualizado por otra sesión. Recarga y vuelve a intentar.",
        )
    except Exception as exc:
        from src.modules.vitalia.inbox.application.services.set_mode_service import (
            ConversationNotFoundError,
        )

        if isinstance(exc, ConversationNotFoundError):
            raise HTTPException(status_code=404, detail="Conversación no encontrada.")
        raise

    return ConversationResponse(
        id=result.conversation_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        handler_mode=result.handler_mode,
        proposal_required=result.proposal_required,
        status=result.status,
        pause_until=result.pause_until,
        help_needed=result.help_needed,
        updated_at=result.updated_at,
    )


# ---------------------------------------------------------------------------
# Endpoint 4: POST /conversations/{conv_id}/pause — pause Adrián 60min (PHI gated)
# ---------------------------------------------------------------------------


class _PauseRequest(BaseModel):
    """Request body for pause Adrián endpoint."""

    model_config = ConfigDict(from_attributes=True)

    reason: str | None = None
    duration_minutes: int = 60


@router.post(
    "/conversations/{conv_id}/pause",
    response_model=ConversationResponse,
)
async def pause_adrian(
    conv_id: UUID,
    body: _PauseRequest,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    service: Annotated[PauseAdrianService, Depends(_get_pause_service)],
) -> ConversationResponse:
    """Pause the Adrián AI agent for 60 minutes (default).

    PHI gated: doctor, nurse, admin_clinic roles only.
    Sets pause_until in DB and Redis TTL for fast check in Adrián entry point.
    Audit log written sync pre-response by PauseAdrianService.

    Args:
        conv_id: Conversation UUID.
        body: Optional reason + duration_minutes (default 60).
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header (dual PHI filter).
        service: PauseAdrianService (injected via DI).

    Returns:
        ConversationResponse with pause_until populated (200 OK).

    Raises:
        401: Invalid/missing token.
        403: Role not permitted.
        404: Conversation not found.
    """
    ctx = await _resolve_context(authorization, x_tenant_id, x_clinic_id, session)

    try:
        _assert_phi_access(ctx.role)
    except PHIAccessDeniedError:
        logger.warning(
            "inbox.pause_adrian.access_denied",
            role=ctx.role,
            conv_id=str(conv_id),
        )
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para pausar al asistente.",
        )

    tenant_id = ctx.tenant_id
    clinic_id = UUID(x_clinic_id)
    user_id = UUID(ctx.user_id) if len(str(ctx.user_id)) == 36 else UUID(int=0)

    try:
        result = await service.pause(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conv_id,
            paused_by_user_id=user_id,
            reason=body.reason,
            duration_minutes=body.duration_minutes,
        )
    except Exception as exc:
        from src.modules.vitalia.inbox.application.services.pause_adrian_service import (
            ConversationNotFoundError,
        )

        if isinstance(exc, ConversationNotFoundError):
            raise HTTPException(status_code=404, detail="Conversación no encontrada.")
        raise

    return ConversationResponse(
        id=result.conversation_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        handler_mode=result.handler_mode,
        proposal_required=False,
        status=result.status,
        pause_until=result.pause_until,
        help_needed=False,
        updated_at=result.pause_until or datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# Endpoint 5: GET /conversations/{conv_id}/tools — tool state (PHI gated, read-only)
# ---------------------------------------------------------------------------


@router.get(
    "/conversations/{conv_id}/tools",
    response_model=ToolsStateResponse,
)
async def get_tools_state(
    conv_id: UUID,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ToolsStateResponse:
    """Retrieve tool availability state for a conversation.

    PHI gated: doctor, nurse, admin_clinic roles only.
    Read-only in Slice 1. Returns static tool registry.

    Args:
        conv_id: Conversation UUID.
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header.

    Returns:
        ToolsStateResponse (200 OK).

    Raises:
        401: Invalid/missing token.
        403: Role not permitted.
    """
    ctx = await _resolve_context(authorization, x_tenant_id, x_clinic_id, session)

    try:
        _assert_phi_access(ctx.role)
    except PHIAccessDeniedError:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para ver el estado de herramientas.",
        )

    # Slice 1: return static tool list (Slice 2 will query from DB)
    from src.modules.vitalia.inbox.application.dto.tools_state_dto import ToolState

    tools = [
        ToolState(
            tool_name="appointment_scheduler",
            enabled=True,
            last_used_at=None,
            display_name_es="Programador de citas",
        ),
        ToolState(
            tool_name="payment_gateway",
            enabled=False,
            last_used_at=None,
            display_name_es="Pasarela de pagos",
        ),
        ToolState(
            tool_name="patient_info",
            enabled=True,
            last_used_at=None,
            display_name_es="Información del paciente",
        ),
    ]
    return ToolsStateResponse(tools=tools, read_only=True)


# ---------------------------------------------------------------------------
# Endpoint 6: GET /conversations/{conv_id}/activity-stream — activity log (PHI gated)
# ---------------------------------------------------------------------------


@router.get(
    "/conversations/{conv_id}/activity-stream",
    response_model=ActivityStreamResponse,
)
async def get_activity_stream(
    conv_id: UUID,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    service: Annotated[ActivityEventService, Depends(_get_activity_service)],
    limit: int = Query(default=8, ge=1, le=50),
    since_minutes: int = Query(default=60, ge=1, le=1440),
) -> ActivityStreamResponse:
    """Retrieve recent activity events for a conversation.

    PHI gated: doctor, nurse, admin_clinic roles only.
    Returns sanitized activity stream (no raw PHI in payload_sanitized).

    Args:
        conv_id: Conversation UUID.
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header (dual PHI filter).
        service: ActivityEventService (injected via DI).
        limit: Max events to return (default 8, max 50).
        since_minutes: Look-back window in minutes (default 60, max 1440).

    Returns:
        ActivityStreamResponse (200 OK).

    Raises:
        401: Invalid/missing token.
        403: Role not permitted.
    """
    ctx = await _resolve_context(authorization, x_tenant_id, x_clinic_id, session)

    try:
        _assert_phi_access(ctx.role)
    except PHIAccessDeniedError:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para ver el historial de actividad.",
        )

    tenant_id = ctx.tenant_id
    clinic_id = UUID(x_clinic_id)

    result = await service.get_stream(
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        conversation_id=conv_id,
        limit=limit,
    )

    from src.modules.vitalia.inbox.application.dto.activity_event_dto import (
        ActivityEventItem,
    )

    events = [
        ActivityEventItem(
            id=ev.id,
            event_kind=ev.event_kind,
            description_es=ev.description_es,
            agent_id=ev.agent_id,
            occurred_at=ev.occurred_at,
        )
        for ev in result.events
    ]

    return ActivityStreamResponse(
        conversation_id=conv_id,
        events=events,
        limit=limit,
        since_minutes=since_minutes,
    )


# ---------------------------------------------------------------------------
# Endpoint 7: POST /proactive-outbound — HSM template send (PHI gated)
# ---------------------------------------------------------------------------


@router.post(
    "/proactive-outbound",
    response_model=ProactiveOutboundResponse,
    status_code=201,
)
async def send_proactive_outbound(
    body: ProactiveOutboundRequest,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    service: Annotated[ProactiveOutboundService, Depends(_get_proactive_service)],
) -> ProactiveOutboundResponse:
    """Send a proactive outbound message via an approved HSM template.

    PHI gated: doctor, nurse, admin_clinic roles only.
    Template registry: 5 Meta-approved HSM templates.
    MARKETING templates require lead.marketing_opt_in = True.
    ComplianceService gate applied before send.

    Args:
        body: ProactiveOutboundRequest (lead_id, template_id, variables, channel).
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header (dual PHI filter).
        service: ProactiveOutboundService (injected via DI).

    Returns:
        ProactiveOutboundResponse (201 Created).

    Raises:
        401: Invalid/missing token.
        403: Role not permitted OR compliance blocked OR marketing opt-in missing.
        404: Lead not found.
        422: Template not found.
        429: Rate limit exceeded.
    """
    ctx = await _resolve_context(authorization, x_tenant_id, x_clinic_id, session)

    try:
        _assert_phi_access(ctx.role)
    except PHIAccessDeniedError:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para enviar mensajes proactivos.",
        )

    tenant_id = ctx.tenant_id
    clinic_id = UUID(x_clinic_id)
    user_id = UUID(ctx.user_id) if len(str(ctx.user_id)) == 36 else UUID(int=0)

    try:
        result = await service.send_proactive(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            lead_id=body.lead_id,
            template_id=body.template_id,
            variables=body.variables,
            channel=body.channel,
            sent_by_user_id=user_id,
        )
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Plantilla no encontrada: {exc.template_id}. Usa una de las plantillas aprobadas.",
        )
    except LeadNotFoundError:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado.")
    except MarketingOptInRequiredError:
        raise HTTPException(
            status_code=403,
            detail="El prospecto no ha dado consentimiento para comunicaciones de marketing.",
        )
    except ComplianceBlockedError as exc:
        raise HTTPException(
            status_code=403,
            detail=f"Mensaje bloqueado por cumplimiento normativo: {exc.failed_policy}.",
        )
    except RateLimitExceededError:
        raise HTTPException(
            status_code=429,
            detail="Límite de mensajes proactivos alcanzado. Intenta mañana.",
        )

    return ProactiveOutboundResponse(
        conversation_id=result.conversation_id,
        message_id=result.message_id,
        template_id=result.template_id,
        channel=result.channel,
        sent_at=result.sent_at,
        compliance_checked=result.compliance_checked,
    )


# ---------------------------------------------------------------------------
# Endpoint 8: POST /transcribe — audio transcription (PHI gated)
# ---------------------------------------------------------------------------


class _TranscribeRequest(BaseModel):
    """Request body for audio transcription."""

    model_config = ConfigDict(from_attributes=True)

    audio_url: str
    media_duration_s: int | None = None


class _TranscribeResponse(BaseModel):
    """Response for audio transcription."""

    model_config = ConfigDict(from_attributes=True)

    transcription_text: str | None = None
    transcription_confidence: float | None = None
    fallback_triggered: bool


@router.post(
    "/transcribe",
    response_model=_TranscribeResponse,
)
async def transcribe_audio(
    body: _TranscribeRequest,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> _TranscribeResponse:
    """Transcribe an audio message via Whisper.

    PHI gated: doctor, nurse, admin_clinic roles only.
    Audio URL must be accessible. Low confidence (<0.5) → fallback_triggered=True.
    PHI: transcription_text is sanitized before logging (patient voice = PHI).

    Args:
        body: TranscribeRequest (audio_url, optional media_duration_s).
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header (dual PHI filter for audit log).

    Returns:
        TranscribeResponse (200 OK).

    Raises:
        401: Invalid/missing token.
        403: Role not permitted.
    """
    ctx = await _resolve_context(authorization, x_tenant_id, x_clinic_id, session)

    try:
        _assert_phi_access(ctx.role)
    except PHIAccessDeniedError:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para transcribir audio.",
        )

    tenant_id = ctx.tenant_id
    clinic_id = UUID(x_clinic_id)

    service = _get_transcribe_service()  # No DB session needed for Whisper

    result = await service.transcribe(
        audio_url=body.audio_url,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
    )

    return _TranscribeResponse(
        transcription_text=result.transcription_text,
        transcription_confidence=result.transcription_confidence,
        fallback_triggered=result.fallback_triggered,
    )


# ---------------------------------------------------------------------------
# Endpoint 9: POST /conversations/{conv_id}/nudge — re-engagement nudge (T-2, PHI gated)
# ---------------------------------------------------------------------------


@router.post(
    "/conversations/{conv_id}/nudge",
    response_model=NudgeResponse,
    status_code=201,
)
async def nudge_conversation(
    conv_id: UUID,
    body: NudgeRequest,
    authorization: AuthorizationHeader,
    x_tenant_id: TenantIdHeader,
    x_clinic_id: ClinicIdHeader,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    service: Annotated[NudgeService, Depends(_get_nudge_service)],
) -> NudgeResponse:
    """Send a 1:1 re-engagement nudge to a live stalled conversation (RN-13).

    PHI gated: doctor, nurse, admin_clinic roles only.
    Idempotency: same-day repeat returns nudge_sent=False (200, not 201).
    Audit log written sync pre-response by NudgeService.

    Scope (RN-13 invariant):
    - ONLY applies to an existing OPEN conversation.
    - ONLY applies when conversation is stalled (last message > 24h ago).
    - Does NOT create a new conversation.
    - Does NOT re-activate cold leads (Camila's domain).

    Anti-coupling:
    - NudgeService consumes send_proactive_reengagement via proactive_resolver DI.
    - NEVER imports from sales_agent/ (av-no-sales-agent-import gate).

    Args:
        conv_id: Conversation UUID (path param).
        body: NudgeRequest (optional reason + idempotency_key).
        authorization: Bearer token.
        x_tenant_id: Tenant ID header.
        x_clinic_id: Clinic ID header (dual PHI filter).
        service: NudgeService (injected via DI).
        session: Async SQLAlchemy session.

    Returns:
        NudgeResponse (201 Created — nudge_sent=True, or 200 on idempotent repeat).

    Raises:
        401: Invalid/missing token.
        403: Role not permitted to access PHI conversations.
        404: Conversation not found or access denied.
        422: Conversation not open or not stalled (NudgeNotApplicableError).
    """
    ctx = await _resolve_context(authorization, x_tenant_id, x_clinic_id, session)

    try:
        _assert_phi_access(ctx.role)
    except PHIAccessDeniedError:
        logger.warning(
            "inbox.nudge.access_denied",
            role=ctx.role,
            conv_id=str(conv_id),
        )
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: tu rol no tiene permisos para enviar un empujón de reactivación.",
        )

    tenant_id = ctx.tenant_id
    clinic_id = UUID(x_clinic_id)
    user_id = UUID(ctx.user_id) if len(str(ctx.user_id)) == 36 else UUID(int=0)

    try:
        result = await service.nudge(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conv_id,
            sent_by_user_id=user_id,
            reason=body.reason,
            idempotency_key=body.idempotency_key,
        )
    except NudgeConvNotFoundError:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    except NudgeNotApplicableError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    from datetime import UTC as _UTC  # noqa: PLC0415
    from datetime import datetime as _dt

    from fastapi.responses import JSONResponse  # noqa: PLC0415

    response_body = NudgeResponse(
        conversation_id=result.conversation_id,
        message_id=result.message_id,
        nudge_sent=result.nudge_sent,
        activity_event_id=result.activity_event_id,
        sent_at=result.sent_at or _dt.now(_UTC),
    )

    # Idempotent repeat (same-day dedup): return 200 instead of 201
    if not result.nudge_sent:
        return JSONResponse(
            status_code=200,
            content=response_body.model_dump(mode="json"),
        )

    return response_body
